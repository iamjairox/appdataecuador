"""Adaptador: CsvParser -- implementa `DocumentParserPort` para CSV.

Streaming real: `csv.reader` itera el archivo linea por linea (nunca
`file.read()` completo); solo se lee un fragmento pequeno por adelantado
para que `csv.Sniffer` detecte el delimitador (coma, punto y coma o
tabulador -- comun encontrar `;` en exports regionales).
"""

from __future__ import annotations

import csv
from typing import TextIO

from govdata.application.dto.resultado_parseo_dto import EstadoParseo, ResultadoParseoDTO
from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.application.ports.document_parser_port import DocumentParserPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import TipoArchivo

logger = get_logger(__name__)

_TAMANO_MUESTRA_SNIFFER = 4096


class CsvParser(DocumentParserPort):
    def soporta(self, tipo_archivo: TipoArchivo) -> bool:
        return tipo_archivo == TipoArchivo.CSV

    def extraer(self, ruta_archivo: str) -> ResultadoParseoDTO:
        try:
            with open(ruta_archivo, encoding="utf-8-sig", newline="") as archivo:
                dialecto = self._detectar_dialecto(archivo)
                lector = csv.reader(archivo, dialecto)

                try:
                    encabezados_raw = next(lector)
                except StopIteration:
                    return ResultadoParseoDTO(
                        estado=EstadoParseo.EXITO,
                        tabla=TablaExtraidaDTO(encabezados=(), filas=[]),
                        mensaje="CSV vacio",
                    )

                encabezados = tuple(celda.strip() for celda in encabezados_raw)
                filas: list[dict[str, str]] = []
                for fila_raw in lector:
                    if not any(celda.strip() for celda in fila_raw):
                        continue
                    filas.append(self._fila_a_dict(encabezados, fila_raw))

            logger.info("csv_extraido", ruta=ruta_archivo, filas=len(filas))
            return ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=TablaExtraidaDTO(encabezados=encabezados, filas=filas))
        except (OSError, UnicodeDecodeError, csv.Error) as exc:
            logger.error("csv_ilegible", ruta=ruta_archivo, error=str(exc))
            return ResultadoParseoDTO(estado=EstadoParseo.ERROR, mensaje=f"CSV corrupto o ilegible: {exc}")

    @staticmethod
    def _detectar_dialecto(archivo: TextIO) -> type[csv.Dialect]:
        muestra = archivo.read(_TAMANO_MUESTRA_SNIFFER)
        archivo.seek(0)
        try:
            return csv.Sniffer().sniff(muestra, delimiters=",;\t")
        except csv.Error:
            return csv.excel

    @staticmethod
    def _fila_a_dict(encabezados: tuple[str, ...], fila_raw: list[str]) -> dict[str, str]:
        return {
            encabezado: (fila_raw[indice].strip() if indice < len(fila_raw) else "")
            for indice, encabezado in enumerate(encabezados)
        }
