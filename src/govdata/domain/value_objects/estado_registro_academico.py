"""Value Object: EstadoRegistroAcademico -- estado de un titulo segun
SENESCYT (Submodulo 7.8: "Registro suspendido", "Registro anulado")."""

from __future__ import annotations

from enum import Enum


class EstadoRegistroAcademico(str, Enum):
    VIGENTE = "vigente"
    SUSPENDIDO = "suspendido"
    ANULADO = "anulado"
    DESCONOCIDO = "desconocido"
