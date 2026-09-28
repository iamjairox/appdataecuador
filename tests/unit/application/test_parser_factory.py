"""Tests: ParserFactory (Submodulo 4.1, patron Strategy)."""

from __future__ import annotations

import pytest

from govdata.application.dto.resultado_parseo_dto import EstadoParseo, ResultadoParseoDTO
from govdata.application.ports.document_parser_port import DocumentParserPort
from govdata.application.services.parser_factory import ParserFactory
from govdata.domain.entities.documento import TipoArchivo
from govdata.domain.exceptions.domain_exceptions import DocumentoNoSoportadoError


class _ParserFalso(DocumentParserPort):
    def __init__(self, tipo: TipoArchivo) -> None:
        self._tipo = tipo

    def soporta(self, tipo_archivo: TipoArchivo) -> bool:
        return tipo_archivo == self._tipo

    def extraer(self, ruta_archivo: str) -> ResultadoParseoDTO:
        return ResultadoParseoDTO(estado=EstadoParseo.EXITO)


def test_selecciona_el_parser_correcto() -> None:
    parser_pdf = _ParserFalso(TipoArchivo.PDF)
    parser_csv = _ParserFalso(TipoArchivo.CSV)
    factory = ParserFactory([parser_pdf, parser_csv])

    assert factory.obtener_parser(TipoArchivo.PDF) is parser_pdf
    assert factory.obtener_parser(TipoArchivo.CSV) is parser_csv


def test_usa_el_primero_que_soporta_sin_ifs_externos() -> None:
    """La fabrica no decide por tipo -- delega en `soporta()` de cada
    estrategia, iterando en orden de registro."""
    parser_generico = _ParserFalso(TipoArchivo.XLSX)
    factory = ParserFactory([parser_generico])
    assert factory.obtener_parser(TipoArchivo.XLSX) is parser_generico


def test_tipo_no_soportado_lanza_error() -> None:
    factory = ParserFactory([_ParserFalso(TipoArchivo.CSV)])
    with pytest.raises(DocumentoNoSoportadoError):
        factory.obtener_parser(TipoArchivo.PDF)


def test_lista_vacia_de_parsers() -> None:
    factory = ParserFactory([])
    with pytest.raises(DocumentoNoSoportadoError):
        factory.obtener_parser(TipoArchivo.CSV)
