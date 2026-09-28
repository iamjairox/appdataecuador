"""Value Object: EstadoRevisionIdentidad -- Submodulo 6.21 (Motor de
Confianza y Revision Manual)."""

from __future__ import annotations

from enum import Enum


class EstadoRevisionIdentidad(str, Enum):
    PENDIENTE_REVISION = "pendiente_revision"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
