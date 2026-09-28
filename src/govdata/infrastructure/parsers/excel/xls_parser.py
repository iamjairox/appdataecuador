"""Adaptador: XlsParser -- implementa `DocumentParserPort` para el
formato binario legado `.xls` (OLE Compound File). `openpyxl` no lee este
formato -- se usa `xlrd`, que SI lo soporta (desde su version 2.x, xlrd
dejo de soportar `.xlsx` a proposito, quedando dedicado a `.xls`).
"""

from __future__ import annotations

import xlrd

from govdata.application.dto.resultado_parseo_dto import EstadoParseo, ResultadoParseoDTO
from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.application.ports.document_parser_port import DocumentParserPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import TipoArchivo

logger = get_logger(__name__)


class XlsParser(DocumentParserPort):
    def soporta(self, tipo_archivo: TipoArchivo) -> bool:
        return tipo_archivo == TipoArchivo.XLS

    def extraer(self, ruta_archivo: str) -> ResultadoParseoDTO:
        try:
            libro = xlrd.open_workbook(ruta_archivo)
            hoja = libro.sheet_by_index(0)
        except Exception as exc:  # noqa: BLE001
            logger.error("xls_ilegible", ruta=ruta_archivo, error=str(exc))
            return ResultadoParseoDTO(estado=EstadoParseo.ERROR, mensaje=f"Excel (.xls) corrupto o ilegible: {exc}")

        if hoja.nrows == 0:
            return ResultadoParseoDTO(
                estado=EstadoParseo.EXITO, tabla=TablaExtraidaDTO(encabezados=(), filas=[]), mensaje="Excel vacio"
            )

        encabezados = tuple(str(valor).strip() for valor in hoja.row_values(0))
        filas: list[dict[str, str]] = []
        for indice_fila in range(1, hoja.nrows):
            valores_crudos = hoja.row_values(indice_fila)
            if not any(str(valor).strip() for valor in valores_crudos):
                continue
            valores = [str(valor).strip() for valor in valores_crudos]
            filas.append(dict(zip(encabezados, valores, strict=False)))

        logger.info("xls_extraido", ruta=ruta_archivo, filas=len(filas))
        return ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=TablaExtraidaDTO(encabezados=encabezados, filas=filas))
