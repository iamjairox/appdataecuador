"""Extraccion de tablas desde PDFs de solo texto (sin lineas de tabla),
usando la estrategia de `pdfplumber` basada en posicion de palabras
(`vertical_strategy="text"`) en vez de lineas dibujadas -- es lo que
permite recuperar columnas en documentos exportados/impresos donde el
texto esta alineado con espacios, no con una tabla real.
"""

from __future__ import annotations

import pdfplumber

from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO

_ESTRATEGIA_TEXTO = {"vertical_strategy": "text", "horizontal_strategy": "text"}


def extraer_via_texto(ruta_archivo: str) -> TablaExtraidaDTO | None:
    filas_crudas: list[list[str | None]] = []
    with pdfplumber.open(ruta_archivo) as pdf:
        for pagina in pdf.pages:
            for tabla in pagina.extract_tables(_ESTRATEGIA_TEXTO):
                filas_crudas.extend(tabla)
    return _filas_a_tabla(filas_crudas)


def _filas_a_tabla(filas_crudas: list[list[str | None]]) -> TablaExtraidaDTO | None:
    filas_no_vacias = [fila for fila in filas_crudas if any((celda or "").strip() for celda in fila)]
    if len(filas_no_vacias) < 2:
        return None

    encabezados = tuple((celda or "").strip() for celda in filas_no_vacias[0])
    filas: list[dict[str, str]] = []
    for fila in filas_no_vacias[1:]:
        if len(fila) != len(encabezados):
            continue
        valores = [(celda or "").strip() for celda in fila]
        filas.append(dict(zip(encabezados, valores, strict=False)))

    if not filas:
        return None
    return TablaExtraidaDTO(encabezados=encabezados, filas=filas)
