"""Value Object: DecisionFusion -- veredicto del Motor de Confianza y
Revision Manual (Submodulo 6.21) sobre un par de identidades candidatas."""

from __future__ import annotations

from enum import Enum


class DecisionFusion(str, Enum):
    FUSION_AUTOMATICA = "fusion_automatica"       # score >= umbral_fusion_automatica
    REVISION_MANUAL = "revision_manual"           # umbral_revision_manual <= score < umbral_fusion_automatica
    MANTENER_SEPARADAS = "mantener_separadas"     # score < umbral_revision_manual
