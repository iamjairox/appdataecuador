"""Value Object: EstadoPaso -- resultado de UN paso del pipeline dinamico
(Submodulos 9.2/9.10/9.15) para un `TrabajoOrquestador` dado."""

from __future__ import annotations

from enum import Enum


class EstadoPaso(str, Enum):
    EJECUTADO = "ejecutado"
    OMITIDO = "omitido"
    FALLIDO = "fallido"
