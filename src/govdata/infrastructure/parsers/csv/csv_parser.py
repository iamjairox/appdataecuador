"""Adaptador: CsvParser -- implementa `DocumentParserPort` para CSV.

Streaming real: `csv.reader` itera el archivo linea por linea (nunca
`file.read()` completo); solo se lee un fragmento pequeno por adelantado
para que `csv.Sniffer` detecte el delimitador (coma, punto y coma o
tabulador -- comun encontrar `;` en exports regionales).

Codificacion: un muestreo real del numeral 2 del portal DPE (24 entidades,
2026-09-27) encontro 10 archivos en Windows-1252 (exportados desde Excel
en Windows), no en UTF-8. Se valida UTF-8 con un decodificador
incremental sobre todo el archivo (en bloques, sin cargarlo entero) y, si
falla, se usa cp1252; latin-1 queda como ultimo recurso (nunca falla).

Encabezado: con `reglas_normalizacion` inyectadas se busca la fila de
encabezado entre las primeras filas (`detector_encabezado.py`) en vez de
asumir la primera; sin reglas se conserva el comportamiento historico.
"""

from __future__ import annotations

import codecs
import csv
import itertools
from typing import TextIO

from govdata.application.dto.resultado_parseo_dto import EstadoParseo, ResultadoParseoDTO
from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.application.ports.document_parser_port import DocumentParserPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import TipoArchivo
from govdata.domain.rules.detector_encabezado import (
    FILAS_BUSQUEDA_ENCABEZADO,
    detectar_fila_encabezado,
    encabezados_unicos,
    limpiar_celda_encabezado,
)
from govdata.domain.rules.reglas_configurables import ReglasNormalizacion

logger = get_logger(__name__)

_TAMANO_MUESTRA_SNIFFER = 4096
_TAMANO_BLOQUE_DETECCION = 64 * 1024
_CODIFICACIONES_RESPALDO = ("cp1252", "latin-1")
# Bytes de control que un CSV de texto nunca contiene (se permiten \t \n \r,
# \x0c y \x1a -- este ultimo lo agregan algunos exports antiguos de Windows).
_BYTES_BINARIOS = frozenset(range(0x20)) - {0x09, 0x0A, 0x0C, 0x0D, 0x1A}


class ContenidoBinarioError(ValueError):
    """El archivo no es texto: latin-1 lo "decodificaria" igual, asi que se
    detecta antes para no convertir basura binaria en filas."""


def detectar_codificacion(ruta_archivo: str) -> str:
    """`utf-8-sig` si TODO el archivo es UTF-8 valido; si no, la primera
    codificacion de respaldo que lo decodifique. Lanza
    `ContenidoBinarioError` si el archivo contiene bytes de control."""
    decodificador = codecs.getincrementaldecoder("utf-8")(errors="strict")
    es_utf8 = True
    with open(ruta_archivo, "rb") as archivo:
        while bloque := archivo.read(_TAMANO_BLOQUE_DETECCION):
            if not _BYTES_BINARIOS.isdisjoint(bloque):
                raise ContenidoBinarioError("el archivo contiene bytes binarios, no es un CSV de texto")
            if es_utf8:
                try:
                    decodificador.decode(bloque)
                except UnicodeDecodeError:
                    es_utf8 = False
    if es_utf8:
        try:
            decodificador.decode(b"", final=True)
            return "utf-8-sig"
        except UnicodeDecodeError:
            pass
    for codificacion in _CODIFICACIONES_RESPALDO:
        decodificador_respaldo = codecs.getincrementaldecoder(codificacion)(errors="strict")
        try:
            with open(ruta_archivo, "rb") as archivo:
                while bloque := archivo.read(_TAMANO_BLOQUE_DETECCION):
                    decodificador_respaldo.decode(bloque)
            return codificacion
        except UnicodeDecodeError:
            continue
    return "latin-1"


class CsvParser(DocumentParserPort):
    def __init__(self, reglas_normalizacion: ReglasNormalizacion | None = None) -> None:
        self._reglas_normalizacion = reglas_normalizacion

    def soporta(self, tipo_archivo: TipoArchivo) -> bool:
        return tipo_archivo == TipoArchivo.CSV

    def extraer(self, ruta_archivo: str) -> ResultadoParseoDTO:
        try:
            codificacion = detectar_codificacion(ruta_archivo)
            with open(ruta_archivo, encoding=codificacion, newline="") as archivo:
                dialecto = self._detectar_dialecto(archivo)
                lector = csv.reader(archivo, dialecto)

                primeras = list(itertools.islice(lector, FILAS_BUSQUEDA_ENCABEZADO))
                if not primeras:
                    return ResultadoParseoDTO(
                        estado=EstadoParseo.EXITO,
                        tabla=TablaExtraidaDTO(encabezados=(), filas=[]),
                        mensaje="CSV vacio",
                    )

                indice_encabezado = 0
                if self._reglas_normalizacion is not None:
                    indice_encabezado = detectar_fila_encabezado(primeras, self._reglas_normalizacion).indice_fila

                encabezados = encabezados_unicos([limpiar_celda_encabezado(c) for c in primeras[indice_encabezado]])
                filas: list[dict[str, str]] = []
                for fila_raw in itertools.chain(primeras[indice_encabezado + 1 :], lector):
                    if not any(celda.strip() for celda in fila_raw):
                        continue
                    filas.append(self._fila_a_dict(encabezados, fila_raw))

            logger.info(
                "csv_extraido",
                ruta=ruta_archivo,
                filas=len(filas),
                codificacion=codificacion,
                fila_encabezado=indice_encabezado + 1,
            )
            return ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=TablaExtraidaDTO(encabezados=encabezados, filas=filas))
        except (OSError, UnicodeDecodeError, ContenidoBinarioError, csv.Error) as exc:
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
