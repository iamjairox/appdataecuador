"""Value Object: NivelPrioridadEjecucion -- Submodulo 9.5 (Motor de
Prioridades). Catalogo cerrado y EXACTO pedido por la especificacion --
deliberadamente distinto de `NivelCriticidad` (Modulo 5, que clasifica la
severidad de un CAMBIO detectado, no el orden de ejecucion de una
ENTIDAD en la cola)."""

from __future__ import annotations

from enum import Enum


class NivelPrioridadEjecucion(str, Enum):
    MUY_ALTA = "muy_alta"
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


_ORDEN: dict[NivelPrioridadEjecucion, int] = {
    NivelPrioridadEjecucion.BAJA: 0,
    NivelPrioridadEjecucion.MEDIA: 1,
    NivelPrioridadEjecucion.ALTA: 2,
    NivelPrioridadEjecucion.MUY_ALTA: 3,
}


def es_mas_prioritario(a: NivelPrioridadEjecucion, b: NivelPrioridadEjecucion) -> bool:
    """True si `a` debe ejecutarse ANTES que `b`."""
    return _ORDEN[a] > _ORDEN[b]
