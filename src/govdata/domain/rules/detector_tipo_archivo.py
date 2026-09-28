"""Regla de dominio: deteccion del tipo de archivo por extension.

Pura: no descarga nada, no inspecciona contenido -- solo interpreta la
extension de una URL o nombre de archivo. Es deliberadamente conservadora:
si la extension no es reconocida, retorna `None` en vez de adivinar (el
caso de uso decide entonces si tratarlo como error o advertencia).
"""

from __future__ import annotations

import re

from govdata.domain.entities.documento import TipoArchivo

_PATRON_EXTENSION = re.compile(r"\.([a-zA-Z0-9]+)(?:[?#]|$)")


def detectar_tipo_por_extension(url_o_nombre: str) -> TipoArchivo | None:
    """Extrae la extension de `url_o_nombre` (ignorando query string/fragment)
    y la mapea a `TipoArchivo`. Retorna None si no hay extension reconocida.
    """
    coincidencia = _PATRON_EXTENSION.search(url_o_nombre)
    if not coincidencia:
        return None

    extension = coincidencia.group(1).lower()
    try:
        return TipoArchivo(extension)
    except ValueError:
        return None
