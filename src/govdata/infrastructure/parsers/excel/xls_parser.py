"""Adaptador: XlsParser -- implementa `DocumentParserPort` para el
formato binario legado `.xls` (OLE Compound File). `openpyxl` no lee este
formato -- se usa `xlrd`, que SI lo soporta (desde su version 2.x, xlrd
dejo de soportar `.xlsx` a proposito, quedando dedicado a `.xls`).

Con `reglas_normalizacion` inyectadas elige la hoja y la fila de
encabezado reales (`detector_encabezado.py`: titulos institucionales,
portadas en la primera hoja, etc.); sin reglas conserva el
comportamiento historico (primera hoja, primera fila).
"""

from __future__ import annotations

import xlrd

from govdata.application.dto.resultado_parseo_dto import EstadoParseo, ResultadoParseoDTO
from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.application.ports.document_parser_port import DocumentParserPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import TipoArchivo
from govdata.domain.rules.detector_encabezado import (
    FILAS_BUSQUEDA_ENCABEZADO,
    EncabezadoDetectado,
    encabezados_unicos,
    limpiar_celda_encabezado,
    seleccionar_hoja_y_encabezado,
)
from govdata.domain.rules.reglas_configurables import ReglasNormalizacion

logger = get_logger(__name__)


class XlsParser(DocumentParserPort):
    def __init__(self, reglas_normalizacion: ReglasNormalizacion | None = None) -> None:
        self._reglas_normalizacion = reglas_normalizacion

    def soporta(self, tipo_archivo: TipoArchivo) -> bool:
        return tipo_archivo == TipoArchivo.XLS

    def extraer(self, ruta_archivo: str) -> ResultadoParseoDTO:
        try:
            libro = xlrd.open_workbook(ruta_archivo)
            deteccion = self._detectar_encabezado(libro)
            hoja = libro.sheet_by_index(deteccion.indice_hoja)
        except Exception as exc:  # noqa: BLE001
            logger.error("xls_ilegible", ruta=ruta_archivo, error=str(exc))
            return ResultadoParseoDTO(estado=EstadoParseo.ERROR, mensaje=f"Excel (.xls) corrupto o ilegible: {exc}")

        if hoja.nrows == 0:
            return ResultadoParseoDTO(
                estado=EstadoParseo.EXITO, tabla=TablaExtraidaDTO(encabezados=(), filas=[]), mensaje="Excel vacio"
            )

        encabezados = encabezados_unicos(
            [limpiar_celda_encabezado(valor) for valor in hoja.row_values(deteccion.indice_fila)]
        )
        filas: list[dict[str, str]] = []
        for indice_fila in range(deteccion.indice_fila + 1, hoja.nrows):
            valores_crudos = hoja.row_values(indice_fila)
            if not any(str(valor).strip() for valor in valores_crudos):
                continue
            valores = [str(valor).strip() for valor in valores_crudos]
            filas.append(dict(zip(encabezados, valores, strict=False)))

        logger.info(
            "xls_extraido",
            ruta=ruta_archivo,
            filas=len(filas),
            hoja=deteccion.indice_hoja,
            fila_encabezado=deteccion.indice_fila + 1,
        )
        return ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=TablaExtraidaDTO(encabezados=encabezados, filas=filas))

    def _detectar_encabezado(self, libro: xlrd.book.Book) -> EncabezadoDetectado:
        if self._reglas_normalizacion is None:
            return EncabezadoDetectado(indice_hoja=0, indice_fila=0, reconocidos=0)
        muestras = []
        for indice_hoja in range(libro.nsheets):
            hoja = libro.sheet_by_index(indice_hoja)
            muestras.append([hoja.row_values(i) for i in range(min(hoja.nrows, FILAS_BUSQUEDA_ENCABEZADO))])
        return seleccionar_hoja_y_encabezado(muestras, self._reglas_normalizacion)
