"""Servicio: ParserFactory -- Submodulo 4.1.

Fabrica que elige automaticamente el parser correcto (patron Strategy).
Deliberadamente NO hay un `if tipo == PDF: ... elif tipo == XLSX: ...`:
cada parser SABE si se soporta a si mismo (`DocumentParserPort.soporta`),
y la fabrica solo itera la lista de estrategias registradas hasta
encontrar la primera que acepte. Agregar un formato nuevo (ej. `.ods` en
el futuro) es registrar una clase nueva en el `Container`, sin tocar esta
fabrica ni ningun `if` existente.
"""

from __future__ import annotations

from govdata.application.ports.document_parser_port import DocumentParserPort
from govdata.domain.entities.documento import TipoArchivo
from govdata.domain.exceptions.domain_exceptions import DocumentoNoSoportadoError


class ParserFactory:
    """Selecciona el `DocumentParserPort` adecuado para un `TipoArchivo`."""

    def __init__(self, parsers: list[DocumentParserPort]) -> None:
        self._parsers = parsers

    def obtener_parser(self, tipo_archivo: TipoArchivo) -> DocumentParserPort:
        for parser in self._parsers:
            if parser.soporta(tipo_archivo):
                return parser
        raise DocumentoNoSoportadoError(
            f"No hay ningun parser registrado que soporte el tipo '{tipo_archivo.value}'"
        )
