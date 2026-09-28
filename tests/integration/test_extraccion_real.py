"""Test de integracion end-to-end: `ExtraerDocumentoUseCase` con
componentes REALES completos -- parsers reales (camelot/pdfplumber/
openpyxl/csv.Sniffer) contra las fixtures binarias reales, Rule Engine
real (YAML de `config/rules/`), y repositorios SQLAlchemy reales contra
SQLite. Es el equivalente, para el Modulo 4, de `test_smoke_descarga.py`
en el Modulo 3: ejercita la cadena completa Parser -> Normalizador ->
Clasificador -> Fingerprint -> Persistencia -> `ResultadoUnificadoDTO`
sin sustituir NINGUNA pieza del Motor de Extraccion por un fake.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from govdata.application.services.parser_factory import ParserFactory
from govdata.application.use_cases.extraer_documento_use_case import (
    DocumentoRequiereOcrError,
    ExtraerDocumentoUseCase,
)
from govdata.config.rule_engine import cargar_rule_engine
from govdata.domain.entities.documento import DocumentoTransparencia, TipoArchivo
from govdata.domain.entities.entidad import Entidad
from govdata.domain.exceptions.domain_exceptions import ExtraccionFallidaError
from govdata.infrastructure.parsers.csv.csv_parser import CsvParser
from govdata.infrastructure.parsers.excel.xls_parser import XlsParser
from govdata.infrastructure.parsers.excel.xlsx_parser import XlsxParser
from govdata.infrastructure.parsers.pdf.pdf_parser_engine import PdfParserEngine
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_repository import (
    SqlAlchemyFuncionarioRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "extraccion"

_RULE_ENGINE = cargar_rule_engine()

# Cargos esperados a partir de `_FILAS_DIRECTORIO` en `_generar.py`:
# Director Juridico y Asesora Juridica -> juridica; Director Financiero ->
# financiera; Contadora y Chofer se descartan (no estan en el catalogo).
_CARGOS_ESPERADOS = {"Director Juridico", "Asesora Juridica", "Director Financiero"}


_contador_publicaciones = iter(range(1, 10_000))


def _entidad_y_documento(sesion, tipo: TipoArchivo, nombre_archivo: str) -> tuple[Entidad, DocumentoTransparencia]:
    from govdata.infrastructure.persistence.postgresql.mappers import (
        documento_mapper,
        entidad_mapper,
    )

    publicacion_id = next(_contador_publicaciones)
    entidad_modelo = EntidadModel(
        nombre="Entidad de Prueba",
        url_transparencia=f"https://x/{nombre_archivo}/{publicacion_id}",
        portal_origen="dpe",
    )
    sesion.add(entidad_modelo)
    sesion.flush()

    documento_modelo = DocumentoModel(
        publicacion_id=publicacion_id,
        tipo_archivo=tipo,
        nombre_original=nombre_archivo,
        url_documento=f"https://x/{nombre_archivo}/{publicacion_id}",
        hash_sha256="a" * 64,
        version=1,
    )
    sesion.add(documento_modelo)
    sesion.flush()

    return entidad_mapper.a_dominio(entidad_modelo), documento_mapper.a_dominio(documento_modelo)


def _caso_uso(sesion) -> ExtraerDocumentoUseCase:
    factory = ParserFactory([PdfParserEngine(), XlsxParser(), XlsParser(), CsvParser()])
    return ExtraerDocumentoUseCase(
        parser_factory=factory,
        rule_engine=_RULE_ENGINE,
        persona_repository=SqlAlchemyPersonaRepository(sesion),
        funcionario_repository=SqlAlchemyFuncionarioRepository(sesion),
    )


class TestExtraccionEndToEndPorFormato:
    @pytest.mark.parametrize(
        "tipo,archivo",
        [
            (TipoArchivo.PDF, "directorio_con_tabla.pdf"),
            (TipoArchivo.PDF, "directorio_con_texto.pdf"),
            (TipoArchivo.XLSX, "directorio.xlsx"),
            (TipoArchivo.CSV, "directorio.csv"),
        ],
    )
    def test_pipeline_completo_clasifica_y_persiste(self, sesion, tipo: TipoArchivo, archivo: str) -> None:
        entidad, documento = _entidad_y_documento(sesion, tipo, archivo)
        caso_uso = _caso_uso(sesion)

        resultado = caso_uso.ejecutar(entidad, documento, str(FIXTURES / archivo), date(2026, 6, 1))
        sesion.flush()

        assert resultado.entidad.nombre == "Entidad de Prueba"
        assert resultado.documento.id == documento.id
        cargos = {f.cargo for f in resultado.funcionarios}
        assert cargos == _CARGOS_ESPERADOS
        # Todo funcionario del contrato unificado trae fingerprint no vacio.
        assert all(f.fingerprint for f in resultado.funcionarios)
        # Persistencia real: debe poder recuperarse via el repositorio.
        persistidos = SqlAlchemyFuncionarioRepository(sesion).listar_por_documento(documento.id)
        assert len(persistidos) == len(_CARGOS_ESPERADOS)


class TestExtraccionEndToEndCasosLimite:
    def test_pdf_escaneado_lanza_requiere_ocr(self, sesion) -> None:
        entidad, documento = _entidad_y_documento(sesion, TipoArchivo.PDF, "directorio_escaneado.pdf")
        caso_uso = _caso_uso(sesion)
        with pytest.raises(DocumentoRequiereOcrError):
            caso_uso.ejecutar(entidad, documento, str(FIXTURES / "directorio_escaneado.pdf"), date(2026, 6, 1))

    def test_documento_corrupto_lanza_extraccion_fallida(self, sesion) -> None:
        entidad, documento = _entidad_y_documento(sesion, TipoArchivo.PDF, "corrupto.pdf")
        caso_uso = _caso_uso(sesion)
        with pytest.raises(ExtraccionFallidaError):
            caso_uso.ejecutar(entidad, documento, str(FIXTURES / "corrupto.pdf"), date(2026, 6, 1))

    def test_columnas_desconocidas_no_detiene_el_pipeline_y_no_produce_funcionarios(self, sesion) -> None:
        entidad, documento = _entidad_y_documento(sesion, TipoArchivo.XLSX, "columnas_desconocidas.xlsx")
        caso_uso = _caso_uso(sesion)
        resultado = caso_uso.ejecutar(entidad, documento, str(FIXTURES / "columnas_desconocidas.xlsx"), date(2026, 6, 1))
        assert resultado.funcionarios == []

    def test_excel_vacio_produce_cero_funcionarios_sin_error(self, sesion) -> None:
        entidad, documento = _entidad_y_documento(sesion, TipoArchivo.XLSX, "excel_vacio.xlsx")
        caso_uso = _caso_uso(sesion)
        resultado = caso_uso.ejecutar(entidad, documento, str(FIXTURES / "excel_vacio.xlsx"), date(2026, 6, 1))
        assert resultado.funcionarios == []

    def test_csv_vacio_produce_cero_funcionarios_sin_error(self, sesion) -> None:
        entidad, documento = _entidad_y_documento(sesion, TipoArchivo.CSV, "csv_vacio.csv")
        caso_uso = _caso_uso(sesion)
        resultado = caso_uso.ejecutar(entidad, documento, str(FIXTURES / "csv_vacio.csv"), date(2026, 6, 1))
        assert resultado.funcionarios == []

    def test_xls_legado_incompleto_lanza_extraccion_fallida(self, sesion) -> None:
        entidad, documento = _entidad_y_documento(sesion, TipoArchivo.XLS, "legado_incompleto.xls")
        caso_uso = _caso_uso(sesion)
        with pytest.raises(ExtraccionFallidaError):
            caso_uso.ejecutar(entidad, documento, str(FIXTURES / "legado_incompleto.xls"), date(2026, 6, 1))


class TestDeduplicacionPorFingerprint:
    def test_misma_persona_en_dos_documentos_no_duplica_persona(self, sesion) -> None:
        """Extraer el mismo directorio dos veces (dos documentos distintos,
        p.ej. dos meses) no debe crear dos filas de `Persona` -- el
        fingerprint debe deduplicar (Submodulo 4.4)."""
        entidad, documento_1 = _entidad_y_documento(sesion, TipoArchivo.XLSX, "directorio.xlsx")
        caso_uso = _caso_uso(sesion)
        caso_uso.ejecutar(entidad, documento_1, str(FIXTURES / "directorio.xlsx"), date(2026, 6, 1))
        sesion.flush()

        _, documento_2 = _entidad_y_documento(sesion, TipoArchivo.CSV, "directorio.csv")
        caso_uso.ejecutar(entidad, documento_2, str(FIXTURES / "directorio.csv"), date(2026, 7, 1))
        sesion.flush()

        from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel

        total_personas = sesion.query(PersonaModel).count()
        # 3 personas relevantes (Juridico x2 + Financiero x1), reutilizadas
        # entre los dos documentos -- nunca 6.
        assert total_personas == len(_CARGOS_ESPERADOS)
