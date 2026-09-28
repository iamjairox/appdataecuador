"""Test de rendimiento: `ExtraerDocumentoUseCase` con MILES de filas
sinteticas -- ejercita el pipeline real completo (Normalizador ->
Clasificador -> Fingerprint -> Persistencia SQLAlchemy/SQLite), con un
parser fake que produce el `TablaExtraidaDTO` en memoria (el costo de
leer un PDF/XLSX real de miles de filas es una propiedad de la libreria
de terceros, no del Motor de Extraccion; lo que este test mide es el
propio pipeline de dominio + persistencia).

No hay un umbral "oficial" de duracion en la especificacion del usuario
-- el limite usado aqui es deliberadamente holgado (30s para 5000 filas
en SQLite) para no volver la suite fragil en maquinas lentas de CI,
mientras sigue detectando una regresion algoritmica real (ej. un
`O(n^2)` accidental en la deduplicacion por fingerprint).
"""

from __future__ import annotations

import time
from datetime import date

from govdata.application.dto.resultado_parseo_dto import EstadoParseo, ResultadoParseoDTO
from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.application.ports.document_parser_port import DocumentParserPort
from govdata.application.services.parser_factory import ParserFactory
from govdata.application.use_cases.extraer_documento_use_case import ExtraerDocumentoUseCase
from govdata.config.rule_engine import cargar_rule_engine
from govdata.domain.entities.documento import TipoArchivo
from govdata.domain.entities.entidad import Entidad
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_repository import (
    SqlAlchemyFuncionarioRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)

_RULE_ENGINE = cargar_rule_engine()

_CARGOS_RELEVANTES = ["Director Juridico", "Asesora Juridica", "Director Financiero"]
_CARGOS_IRRELEVANTES = ["Chofer", "Contadora"]


def _tabla_sintetica(cantidad_filas: int) -> TablaExtraidaDTO:
    """`cantidad_filas` filas, alternando entre cargos relevantes
    (deben clasificarse) e irrelevantes (deben descartarse), cada una
    con nombre unico (para que el fingerprint NO deduplique -- se quiere
    medir el costo de crear muchas `Persona` distintas, el peor caso)."""
    filas = []
    for i in range(cantidad_filas):
        cargo = (_CARGOS_RELEVANTES + _CARGOS_IRRELEVANTES)[i % 5]
        filas.append(
            {
                "Nombre Completo": f"Persona Sintetica Numero{i:06d} Apellido{i:06d}",
                "Cargo": cargo,
                "Dependencia": "Departamento X",
                "Correo": f"persona{i:06d}@entidad.gob.ec",
                "Telefono": f"09{i:08d}"[:10],
            }
        )
    return TablaExtraidaDTO(encabezados=("Nombre Completo", "Cargo", "Dependencia", "Correo", "Telefono"), filas=filas)


class _ParserSinteticoFake(DocumentParserPort):
    """Parser fake: SOLO reemplaza la lectura de bytes (I/O de terceros).
    Todo lo demas (normalizacion, clasificacion, fingerprint,
    persistencia) corre con las implementaciones REALES."""

    def __init__(self, tabla: TablaExtraidaDTO) -> None:
        self._tabla = tabla

    def soporta(self, tipo_archivo: TipoArchivo) -> bool:
        return True

    def extraer(self, ruta_archivo: str) -> ResultadoParseoDTO:
        return ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=self._tabla)


def _entidad_y_documento(sesion) -> tuple[Entidad, object]:
    from govdata.infrastructure.persistence.postgresql.mappers import (
        documento_mapper,
        entidad_mapper,
    )

    entidad_modelo = EntidadModel(nombre="Entidad Rendimiento", url_transparencia="https://x/rendimiento", portal_origen="dpe")
    sesion.add(entidad_modelo)
    sesion.flush()
    documento_modelo = DocumentoModel(
        publicacion_id=1,
        tipo_archivo=TipoArchivo.CSV,
        nombre_original="masivo.csv",
        url_documento="https://x/masivo.csv",
        hash_sha256="b" * 64,
        version=1,
    )
    sesion.add(documento_modelo)
    sesion.flush()
    return entidad_mapper.a_dominio(entidad_modelo), documento_mapper.a_dominio(documento_modelo)


def test_pipeline_procesa_cinco_mil_filas_en_tiempo_razonable(sesion) -> None:
    cantidad_filas = 5_000
    tabla = _tabla_sintetica(cantidad_filas)
    entidad, documento = _entidad_y_documento(sesion)

    caso_uso = ExtraerDocumentoUseCase(
        parser_factory=ParserFactory([_ParserSinteticoFake(tabla)]),
        rule_engine=_RULE_ENGINE,
        persona_repository=SqlAlchemyPersonaRepository(sesion),
        funcionario_repository=SqlAlchemyFuncionarioRepository(sesion),
    )

    inicio = time.perf_counter()
    resultado = caso_uso.ejecutar(entidad, documento, "irrelevante.csv", date(2026, 6, 1))
    duracion = time.perf_counter() - inicio

    # 3 de cada 5 filas usan un cargo relevante.
    esperados = cantidad_filas * len(_CARGOS_RELEVANTES) // 5
    assert len(resultado.funcionarios) == esperados
    assert duracion < 30.0, f"El pipeline tardo {duracion:.2f}s para {cantidad_filas} filas (limite: 30s)"

    tasa = cantidad_filas / duracion
    assert tasa > 50, f"Tasa de procesamiento demasiado baja: {tasa:.1f} filas/segundo"
