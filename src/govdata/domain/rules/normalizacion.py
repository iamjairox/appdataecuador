"""Normalizacion de texto compartida entre reglas de dominio.

Centraliza la misma normalizacion (mayusculas, sin tildes, espacios
colapsados) que usan los Value Objects de nombres, para que el matching
difuso compare siempre sobre texto consistente.
"""

from __future__ import annotations

import re
import unicodedata


def normalizar_texto(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    sin_puntuacion = re.sub(r"[.,;:_/-]", " ", sin_tildes)
    colapsado = re.sub(r"\s+", " ", sin_puntuacion).strip()
    return colapsado.upper()
