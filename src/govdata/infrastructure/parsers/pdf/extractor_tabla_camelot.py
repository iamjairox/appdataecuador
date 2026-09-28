"""Extraccion de tablas PDF via `camelot` (flavor 'stream' -- no requiere
Ghostscript, funciona por analisis de posicion de texto).

Convierte el `DataFrame` de camelot a `TablaExtraidaDTO` INMEDIATAMENTE:
ningun otro modulo del sistema ve jamas un `DataFrame`.
"""

from __future__ import annotations

import camelot
import pandas as pd

from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.config.logging_config import get_logger

logger = get_logger(__name__)


def extraer_via_camelot(ruta_archivo: str) -> TablaExtraidaDTO | None:
    """Retorna la primera tabla con datos utiles, o None si camelot no
    encontro ninguna estructura tabular reconocible."""
    try:
        tablas = camelot.read_pdf(ruta_archivo, flavor="stream", pages="all")
    except Exception as exc:  # noqa: BLE001 - camelot puede lanzar variedad de excepciones internas
        logger.warning("camelot_fallo", ruta=ruta_archivo, error=str(exc))
        return None

    for tabla in tablas:
        resultado = _dataframe_a_tabla(tabla.df)
        if resultado is not None:
            return resultado
    return None


def _dataframe_a_tabla(df: pd.DataFrame) -> TablaExtraidaDTO | None:
    if df.empty or len(df) < 2:
        return None

    encabezados = tuple(str(c).strip() for c in df.iloc[0].tolist())
    if not any(encabezados):
        return None
    if len(encabezados) < 2:
        # Camelot degrada a una sola columna de ancho completo cuando no
        # detecta separacion real entre columnas (comun en PDFs de texto
        # posicionado sin lineas de tabla): eso NO es una tabla util,
        # es la senal de que hay que caer al fallback de texto
        # (`extractor_texto_pdfplumber`), que si distingue columnas por
        # clustering de posicion de palabras.
        return None

    filas: list[dict[str, str]] = []
    for _, fila in df.iloc[1:].iterrows():
        valores = [str(v).strip() for v in fila.tolist()]
        if not any(valores):
            continue
        filas.append(dict(zip(encabezados, valores, strict=False)))

    if not filas:
        return None
    return TablaExtraidaDTO(encabezados=encabezados, filas=filas)
