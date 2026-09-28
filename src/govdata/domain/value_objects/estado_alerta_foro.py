"""Value Object: EstadoAlertaForo -- ciclo de vida de `AlertaForo`
(Submodulo 8.7)."""

from __future__ import annotations

from enum import Enum


class EstadoAlertaForo(str, Enum):
    PENDIENTE = "pendiente"
    ENVIADA = "enviada"
    DESCARTADA = "descartada"
