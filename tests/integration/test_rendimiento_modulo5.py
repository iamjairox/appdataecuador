"""Test de rendimiento: `CompararDocumentosUseCase` con MILES de
funcionarios -- ejercita el pipeline real completo (Motor de Comparacion
-> Persistencia Inteligente -> Historial -> Alertas -> Oportunidades ->
Eventos -> Auditoria) contra SQLite real.

Igual que el equivalente del Modulo 4: no hay un umbral "oficial" en la
especificacion del usuario ("cientos de miles de funcionarios" es la
meta de PRODUCCION, con PostgreSQL + indices reales, no de este test en
SQLite de un solo hilo) -- el limite usado aqui es deliberadamente
holgado para no volver la suite fragil en CI, mientras sigue detectando
una regresion algoritmica real (ej. un `O(n^2)` accidental en el
emparejamiento por fingerprint o en la apertura de versiones)."""

from __future__ import annotations

import time
from datetime import date

from govdata.application.dto.resultado_unificado_dto import FuncionarioUnificadoDTO
from govdata.application.services.alerta_service import AlertaService
from govdata.application.services.auditoria_comparacion_service import AuditoriaComparacionService
from govdata.application.services.evento_service import EventoService
from govdata.application.services.historial_service import HistorialService
from govdata.application.services.oportunidad_comercial_service import OportunidadComercialService
from govdata.application.services.persistencia_inteligente_service import (
    PersistenciaInteligenteService,
)
from govdata.application.use_cases.comparar_documentos_use_case import CompararDocumentosUseCase
from govdata.config.rule_engine import cargar_rule_engine
from govdata.domain.entities.documento import DocumentoTransparencia, EstadoDocumento, TipoArchivo
from govdata.domain.entities.entidad import Entidad
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_auditoria_comparacion_repository import (
    SqlAlchemyAuditoriaComparacionRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_repository import (
    SqlAlchemyEventoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_repository import (
    SqlAlchemyFuncionarioRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_oportunidad_comercial_repository import (
    SqlAlchemyOportunidadComercialRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_version_funcionario_repository import (
    SqlAlchemyVersionFuncionarioRepository,
)

_RULE_ENGINE = cargar_rule_engine()
_CARGOS = ["Director Juridico", "Abogado", "Chofer", "Contador", "Asistente"]


def _tabla_sintetica(cantidad: int) -> list[FuncionarioUnificadoDTO]:
    return [
        FuncionarioUnificadoDTO(
            nombre=f"Persona{i:06d}", apellido=f"Apellido{i:06d}", cargo=_CARGOS[i % len(_CARGOS)],
            dependencia="Departamento X", correo=f"persona{i:06d}@x.gob.ec",
            telefono=f"09{i:08d}"[:10], area="juridica", score=90.0, fingerprint=f"FP{i:06d}",
        )
        for i in range(cantidad)
    ]


def _caso_uso(sesion) -> CompararDocumentosUseCase:
    persona_repo = SqlAlchemyPersonaRepository(sesion)
    funcionario_repo = SqlAlchemyFuncionarioRepository(sesion)
    version_repo = SqlAlchemyVersionFuncionarioRepository(sesion)
    alerta_repo = SqlAlchemyAlertaRepository(sesion)
    evento_repo = SqlAlchemyEventoRepository(sesion)
    auditoria_repo = SqlAlchemyAuditoriaComparacionRepository(sesion)
    oportunidad_repo = SqlAlchemyOportunidadComercialRepository(sesion)

    historial = HistorialService(version_repo)
    persistencia = PersistenciaInteligenteService(persona_repo, funcionario_repo, historial)
    alerta_service = AlertaService(alerta_repo, _RULE_ENGINE.criticidad)
    oportunidad_service = OportunidadComercialService(oportunidad_repo, _RULE_ENGINE.criticidad)
    evento_service = EventoService(evento_repo)
    auditoria_service = AuditoriaComparacionService(auditoria_repo)

    return CompararDocumentosUseCase(persistencia, alerta_service, oportunidad_service, evento_service, auditoria_service, _RULE_ENGINE)


def _entidad_y_documento(sesion) -> tuple[Entidad, DocumentoTransparencia]:
    from govdata.infrastructure.persistence.postgresql.mappers import (
        documento_mapper,
        entidad_mapper,
    )

    entidad_modelo = EntidadModel(nombre="Entidad Rendimiento M5", url_transparencia="https://x/rendimiento5", portal_origen="dpe")
    sesion.add(entidad_modelo)
    sesion.flush()
    documento_modelo = DocumentoModel(
        publicacion_id=1, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf", url_documento="https://x/d.pdf",
        estado=EstadoDocumento.DESCARGADO, hash_sha256="a" * 64, tamano_bytes=10, ruta_almacenamiento="file:///a", version=1,
    )
    sesion.add(documento_modelo)
    sesion.flush()
    return entidad_mapper.a_dominio(entidad_modelo), documento_mapper.a_dominio(documento_modelo)


def test_primera_comparacion_con_cinco_mil_funcionarios_nuevos(sesion) -> None:
    """Peor caso de insercion: 5000 funcionarios, TODOS nuevos (sin
    version anterior) -- cada uno dispara Persona+Funcionario+VersionFuncionario."""
    cantidad = 5_000
    actuales = _tabla_sintetica(cantidad)
    entidad, documento = _entidad_y_documento(sesion)
    caso_uso = _caso_uso(sesion)

    inicio = time.perf_counter()
    resultado = caso_uso.ejecutar(entidad, None, documento, [], actuales, mes_publicado_actual=date(2026, 6, 1))
    duracion = time.perf_counter() - inicio

    assert len(resultado.nuevos) == cantidad
    assert duracion < 60.0, f"El pipeline tardo {duracion:.2f}s para {cantidad} funcionarios nuevos (limite: 60s)"
    tasa = cantidad / duracion
    assert tasa > 20, f"Tasa de procesamiento demasiado baja: {tasa:.1f} funcionarios/segundo"


def test_comparacion_con_cambios_parciales_sobre_cinco_mil_funcionarios(sesion) -> None:
    """Segundo caso: los mismos 5000 ya existen (sin cambios), mas un 10%
    con cambio de cargo -- mide el costo real de re-comparar un lote
    grande, no solo de insertar."""
    cantidad = 5_000
    anteriores = _tabla_sintetica(cantidad)
    entidad, documento_1 = _entidad_y_documento(sesion)
    caso_uso = _caso_uso(sesion)
    caso_uso.ejecutar(entidad, None, documento_1, [], anteriores, mes_publicado_actual=date(2026, 6, 1))
    sesion.flush()

    actuales = _tabla_sintetica(cantidad)
    for i in range(0, cantidad, 10):  # 10% cambia de cargo
        actuales[i] = FuncionarioUnificadoDTO(
            nombre=actuales[i].nombre, apellido=actuales[i].apellido, cargo="Director Financiero",
            dependencia=actuales[i].dependencia, correo=actuales[i].correo, telefono=actuales[i].telefono,
            area="financiera", score=90.0, fingerprint=actuales[i].fingerprint,
        )

    from govdata.infrastructure.persistence.postgresql.mappers import documento_mapper
    from govdata.infrastructure.persistence.postgresql.models.documento_model import (
        DocumentoModel as _DM,
    )

    documento_2_modelo = _DM(
        publicacion_id=2, tipo_archivo=TipoArchivo.PDF, nombre_original="d2.pdf", url_documento="https://x/d2.pdf",
        estado=EstadoDocumento.DESCARGADO, hash_sha256="b" * 64, tamano_bytes=10, ruta_almacenamiento="file:///b", version=1,
    )
    sesion.add(documento_2_modelo)
    sesion.flush()
    documento_2 = documento_mapper.a_dominio(documento_2_modelo)

    inicio = time.perf_counter()
    resultado = caso_uso.ejecutar(entidad, documento_1, documento_2, anteriores, actuales, mes_publicado_actual=date(2026, 7, 1), mes_publicado_anterior=date(2026, 6, 1))
    duracion = time.perf_counter() - inicio

    assert len(resultado.cambios) == cantidad // 10
    assert len(resultado.sin_cambios) == cantidad - cantidad // 10
    assert duracion < 60.0, f"La re-comparacion tardo {duracion:.2f}s para {cantidad} funcionarios (limite: 60s)"
