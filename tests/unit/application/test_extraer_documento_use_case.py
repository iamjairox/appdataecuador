"""Tests: ExtraerDocumentoUseCase (con parser fake, sin PDFs reales --
ver tests/integration para la validacion con parsers reales)."""

from __future__ import annotations

from datetime import date

import pytest

from govdata.application.dto.resultado_parseo_dto import EstadoParseo, ResultadoParseoDTO
from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.application.ports.document_parser_port import DocumentParserPort
from govdata.application.services.parser_factory import ParserFactory
from govdata.application.use_cases.extraer_documento_use_case import (
    DocumentoRequiereOcrError,
    ExtraerDocumentoUseCase,
)
from govdata.config.rule_engine import cargar_rule_engine
from govdata.domain.entities.documento import DocumentoTransparencia, TipoArchivo
from govdata.domain.entities.entidad import Entidad
from govdata.domain.exceptions.domain_exceptions import ExtraccionFallidaError
from tests.unit.application.fakes_extraccion import (
    FakeFuncionarioRepositoryExtraccion,
    FakePersonaRepository,
)

_RULE_ENGINE = cargar_rule_engine()


class _ParserFake(DocumentParserPort):
    def __init__(self, resultado: ResultadoParseoDTO) -> None:
        self._resultado = resultado

    def soporta(self, tipo_archivo: TipoArchivo) -> bool:
        return True

    def extraer(self, ruta_archivo: str) -> ResultadoParseoDTO:
        return self._resultado


def _entidad() -> Entidad:
    return Entidad(id=1, nombre="Entidad X", url_transparencia="https://x/1", portal_origen="dpe")


def _documento() -> DocumentoTransparencia:
    return DocumentoTransparencia(
        id=10, publicacion_id=1, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf", url_documento="https://x/d.pdf"
    )


def _caso_uso(resultado_parseo: ResultadoParseoDTO):
    factory = ParserFactory([_ParserFake(resultado_parseo)])
    return (
        ExtraerDocumentoUseCase(factory, _RULE_ENGINE, FakePersonaRepository(), FakeFuncionarioRepositoryExtraccion()),
    )


class TestFlujoExitoso:
    def test_extrae_normaliza_clasifica_y_persiste(self) -> None:
        tabla = TablaExtraidaDTO(
            encabezados=("Nombre Completo", "Cargo", "Dependencia", "Correo"),
            filas=[
                {
                    "Nombre Completo": "Juan Carlos Perez Gomez",
                    "Cargo": "Director Juridico",
                    "Dependencia": "Procuraduria",
                    "Correo": "jp@x.gob.ec",
                },
                {
                    "Nombre Completo": "Maria Torres",
                    "Cargo": "Chofer",
                    "Dependencia": "Transporte",
                    "Correo": "",
                },
            ],
        )
        (caso_uso,) = _caso_uso(ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=tabla))

        resultado = caso_uso.ejecutar(_entidad(), _documento(), "ruta/falsa.pdf", date(2026, 6, 1))

        assert resultado.entidad.nombre == "Entidad X"
        assert resultado.documento.id == 10
        assert len(resultado.funcionarios) == 1  # solo el Director Juridico
        assert resultado.funcionarios[0].area == "juridica"
        assert resultado.funcionarios[0].fingerprint == "JUANCARLOSPEREZGOMEZ"

    def test_tabla_vacia_produce_cero_funcionarios(self) -> None:
        tabla = TablaExtraidaDTO(encabezados=(), filas=[])
        (caso_uso,) = _caso_uso(ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=tabla))
        resultado = caso_uso.ejecutar(_entidad(), _documento(), "x.pdf", date(2026, 6, 1))
        assert resultado.funcionarios == []


class TestManejoDeErrores:
    def test_requiere_ocr_lanza_excepcion_especifica(self) -> None:
        (caso_uso,) = _caso_uso(ResultadoParseoDTO(estado=EstadoParseo.REQUIERE_OCR, mensaje="sin texto"))
        with pytest.raises(DocumentoRequiereOcrError):
            caso_uso.ejecutar(_entidad(), _documento(), "x.pdf", date(2026, 6, 1))

    def test_error_de_parseo_lanza_extraccion_fallida(self) -> None:
        (caso_uso,) = _caso_uso(ResultadoParseoDTO(estado=EstadoParseo.ERROR, mensaje="corrupto"))
        with pytest.raises(ExtraccionFallidaError):
            caso_uso.ejecutar(_entidad(), _documento(), "x.pdf", date(2026, 6, 1))

    def test_documento_sin_id_lanza_error(self) -> None:
        (caso_uso,) = _caso_uso(ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=TablaExtraidaDTO(encabezados=(), filas=[])))
        documento_sin_id = DocumentoTransparencia(
            publicacion_id=1, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf", url_documento="https://x/d.pdf"
        )
        with pytest.raises(ExtraccionFallidaError):
            caso_uso.ejecutar(_entidad(), documento_sin_id, "x.pdf", date(2026, 6, 1))

    def test_correo_invalido_no_detiene_el_pipeline(self) -> None:
        """Correo malformado -> Value Object lo descarta (queda None),
        pero la fila SIGUE clasificandose y persistiendo."""
        tabla = TablaExtraidaDTO(
            encabezados=("Nombres", "Apellidos", "Cargo", "Dependencia", "Correo"),
            filas=[
                {
                    "Nombres": "Juan",
                    "Apellidos": "Perez",
                    "Cargo": "Director Juridico",
                    "Dependencia": "X",
                    "Correo": "esto-no-es-un-correo",
                }
            ],
        )
        (caso_uso,) = _caso_uso(ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=tabla))
        resultado = caso_uso.ejecutar(_entidad(), _documento(), "x.pdf", date(2026, 6, 1))
        assert len(resultado.funcionarios) == 1
        assert resultado.funcionarios[0].correo is None

    def test_dependencia_desconocida_usa_placeholder(self) -> None:
        tabla = TablaExtraidaDTO(
            encabezados=("Nombres", "Apellidos", "Cargo"),
            filas=[{"Nombres": "Juan", "Apellidos": "Perez", "Cargo": "Director Juridico"}],
        )
        (caso_uso,) = _caso_uso(ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=tabla))
        resultado = caso_uso.ejecutar(_entidad(), _documento(), "x.pdf", date(2026, 6, 1))
        assert resultado.funcionarios[0].dependencia
