"""DTO: DecisionFusionDTO -- veredicto de `FusionService` (Submodulo
6.14 + 6.21) sobre un par de identidades candidatas, ya ejecutado."""

from __future__ import annotations

from dataclasses import dataclass

from govdata.domain.value_objects.decision_fusion import DecisionFusion


@dataclass(frozen=True, slots=True)
class DecisionFusionDTO:
    decision: DecisionFusion
    score: float
    persona_master_resultante_id: int
    """La PersonaMaster con la que el llamador debe seguir trabajando:
    la ganadora de una fusion automatica, la propia nueva PersonaMaster
    cuando se crea un caso de revision (provisional, EN_REVISION) o se
    mantienen separadas, o la unica candidata cuando no hubo ambiguedad."""
    caso_revision_id: str | None = None
    explicacion: str = ""
