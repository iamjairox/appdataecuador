"""Adaptador: PdfParserEngine -- implementa `DocumentParserPort` para PDF.

Compone (Strategy interno) tres pasos, en orden:

    1. Deteccion de PDF escaneado -> REQUIERE_OCR (nunca se fuerza el
       procesamiento de una imagen sin capa de texto).
    2. Extraccion "PDF con tablas" via camelot (estructuras tabulares
       reales, con o sin lineas dibujadas).
    3. Si camelot no encuentra nada, fallback "PDF con texto" via la
       estrategia de posicion de palabras de pdfplumber.

Se expone como UN solo parser registrado en el `ParserFactory` para
`TipoArchivo.PDF` (la fabrica no necesita saber que hay dos estrategias
internas) -- el Strategy Pattern aplica tanto en el nivel de la fabrica
(que parser por tipo de archivo) como aqui dentro (que tecnica de
extraccion de tabla).
"""

from __future__ import annotations

from govdata.application.dto.resultado_parseo_dto import EstadoParseo, ResultadoParseoDTO
from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.application.ports.document_parser_port import DocumentParserPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import TipoArchivo
from govdata.infrastructure.parsers.pdf.detector_pdf_escaneado import es_pdf_escaneado
from govdata.infrastructure.parsers.pdf.extractor_tabla_camelot import extraer_via_camelot
from govdata.infrastructure.parsers.pdf.extractor_texto_pdfplumber import extraer_via_texto

logger = get_logger(__name__)


class PdfParserEngine(DocumentParserPort):
    def __init__(self, umbral_caracteres_por_pagina: int = 10) -> None:
        self._umbral_caracteres_por_pagina = umbral_caracteres_por_pagina

    def soporta(self, tipo_archivo: TipoArchivo) -> bool:
        return tipo_archivo == TipoArchivo.PDF

    def extraer(self, ruta_archivo: str) -> ResultadoParseoDTO:
        try:
            if es_pdf_escaneado(ruta_archivo, self._umbral_caracteres_por_pagina):
                logger.info("pdf_requiere_ocr", ruta=ruta_archivo)
                return ResultadoParseoDTO(
                    estado=EstadoParseo.REQUIERE_OCR,
                    mensaje="PDF sin capa de texto detectable (posible escaneo)",
                )
        except Exception as exc:  # noqa: BLE001 - cualquier fallo al abrir es "documento corrupto"
            logger.error("pdf_ilegible", ruta=ruta_archivo, error=str(exc))
            return ResultadoParseoDTO(estado=EstadoParseo.ERROR, mensaje=f"PDF corrupto o ilegible: {exc}")

        tabla, fuente = self._extraer_con_fallback(ruta_archivo)
        if tabla is None:
            logger.warning("pdf_sin_filas_tabulares", ruta=ruta_archivo)
            return ResultadoParseoDTO(
                estado=EstadoParseo.EXITO,
                tabla=TablaExtraidaDTO(encabezados=(), filas=[]),
                mensaje="El PDF tiene texto pero no se detecto una estructura tabular",
            )

        logger.info("pdf_extraido", ruta=ruta_archivo, fuente=fuente, filas=tabla.cantidad_filas)
        return ResultadoParseoDTO(estado=EstadoParseo.EXITO, tabla=tabla)

    @staticmethod
    def _extraer_con_fallback(ruta_archivo: str) -> tuple[TablaExtraidaDTO | None, str]:
        tabla = extraer_via_camelot(ruta_archivo)
        if tabla is not None:
            return tabla, "camelot-tabla"

        tabla = extraer_via_texto(ruta_archivo)
        if tabla is not None:
            return tabla, "pdfplumber-texto"

        return None, "ninguna"
