"""Evita que identificadores numéricos lleguen a superficies auditables."""

from __future__ import annotations

import re

_CEDULA = re.compile(r"(?<!\d)\d{10}(?!\d)")


def sanitizar_error_externo(error: BaseException | str) -> str:
    return _CEDULA.sub("[IDENTIFICADOR_REDACTADO]", str(error))
