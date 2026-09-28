"""Deteccion de PDF escaneado (sin capa de texto).

No es una regla de dominio pura porque necesita abrir el archivo (IO);
vive en infraestructura, usada exclusivamente por `PdfParserEngine`.
"""

from __future__ import annotations

import pdfplumber

UMBRAL_CARACTERES_POR_PAGINA_DEFECTO = 10


def es_pdf_escaneado(
    ruta_archivo: str, umbral_caracteres_por_pagina: int = UMBRAL_CARACTERES_POR_PAGINA_DEFECTO
) -> bool:
    """True si el promedio de caracteres de texto extraible por pagina
    esta por debajo del umbral -- senal de que el PDF es una imagen
    escaneada sin capa de texto (OCR), no un documento de texto real.
    """
    with pdfplumber.open(ruta_archivo) as pdf:
        if not pdf.pages:
            return False
        total_caracteres = sum(len(pagina.extract_text() or "") for pagina in pdf.pages)
        promedio = total_caracteres / len(pdf.pages)
    return promedio < umbral_caracteres_por_pagina
