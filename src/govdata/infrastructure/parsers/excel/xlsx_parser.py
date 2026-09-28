"""Adaptador: XlsxParser -- implementa `DocumentParserPort` para XLSX.

`read_only=True` de openpyxl evita cargar el workbook completo en
memoria: itera filas bajo demanda directamente del XML comprimido.
"""

from __future__ import annotations

import openpyxl

from govdata.application.dto.resultado_parseo_dto import EstadoParseo, ResultadoParseoDTO
from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.application.ports.document_parser_port import DocumentParserPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import TipoArchivo

logger = get_logger(__name__)


class XlsxParser(DocumentParserPort):
    def soporta(self, tipo_archivo: TipoArchivo) -> bool:
        return tipo_archivo == TipoArchivo.XLSX

    def extraer(self, ruta_archivo: str) -> ResultadoParseoDTO:
        try:
            libro = openpyxl.load_workbook(ruta_archivo, read_only=True, data_only=True)
        except Exception as exc:  # noqa: BLE001 - cualquier fallo de apertura es "corrupto"
            logger.error("xlsx_ilegible", ruta=ruta_archivo, error=str(exc))
            return ResultadoParseoDTO(estado=EstadoParseo.ERROR, mensaje=f"Excel (.xlsx) corrupto o ilegible: {exc}")

        try:
            hoja = libro.active
            if hoja is None:
                return ResultadoParseoDTO(
                    estado=EstadoParseo.EXITO,
                    tabla=TablaExtraidaDTO(encabezados=(), filas=[]),
                    mensaje="El libro no tiene ninguna hoja activa",
                )

            filas_iter = hoja.iter_rows(values_only=True)
            try:
                encabezados_raw = next(filas_iter)
            except StopIteration:
                return ResultadoParseoDTO(
                    estado=EstadoParseo.EXITO,
                    tabla=TablaExtraidaDTO(encabezados=(), filas=[]),
                    mensaje="Excel vacio",
                )

            encabezados = tuple(str(celda).strip() if celda is not None else "" for celda in encabezados_raw)
            filas: list[dict[str, str]] = []
            for fila_raw in filas_iter:
                if fila_raw is None or all(celda is None for celda in fila_raw):
                    continue
                valores = [str(celda).strip() if celda is not None else "" for celda in fila_raw]
                filas.append(dict(zip(encabezados, valores, strict=False)))

            logger.info("xlsx_extraido", ruta=ruta_archivo, filas=len(filas))
            return ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=TablaExtraidaDTO(encabezados=encabezados, filas=filas))
        finally:
            libro.close()
