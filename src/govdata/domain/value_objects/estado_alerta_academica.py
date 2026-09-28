"""Value Object: EstadoAlertaAcademica -- ciclo de vida de `AlertaAcademica`
(Submodulo 7.8)."""

from __future__ import annotations

from enum import Enum


class EstadoAlertaAcademica(str, Enum):
    PENDIENTE = "pendiente"
    ENVIADA = "enviada"
    DESCARTADA = "descartada"
