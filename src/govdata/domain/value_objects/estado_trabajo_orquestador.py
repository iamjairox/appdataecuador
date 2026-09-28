"""Value Object: EstadoTrabajoOrquestador -- Submodulo 9.6 (Cola de
Trabajos). Catalogo cerrado y EXACTO pedido por la especificacion --
deliberadamente distinto de `JobStatus` (Modulo 4, congelado, que
describe las FASES internas de un pipeline, no el ciclo de vida de un
item en una cola persistente con pausa/reintento/cancelacion)."""

from __future__ import annotations

from enum import Enum


class EstadoTrabajoOrquestador(str, Enum):
    PENDIENTE = "pendiente"
    EN_COLA = "en_cola"
    EJECUTANDO = "ejecutando"
    PAUSADO = "pausado"
    REINTENTANDO = "reintentando"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"
    ERROR = "error"
