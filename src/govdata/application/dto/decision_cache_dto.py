"""DTO: DecisionCacheDTO -- Submodulo 4.9 (Cache inteligente)."""

from __future__ import annotations

from dataclasses import dataclass

from govdata.domain.entities.documento import DocumentoTransparencia


@dataclass(frozen=True, slots=True)
class DecisionCacheDTO:
    """Veredicto de `CacheService`: usar lo ya persistido o reprocesar."""

    vigente: bool
    motivo: str
    documento: DocumentoTransparencia | None = None
