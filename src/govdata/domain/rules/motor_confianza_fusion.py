"""Regla de dominio: Motor de Confianza y Revision Manual -- Submodulo
6.21 (sugerencia explicita del cliente).

"En sistemas de resolucion de identidad nunca es recomendable fusionar
automaticamente todas las coincidencias":

    score >= umbral_fusion_automatica (98%)                -> FUSION_AUTOMATICA
    umbral_revision_manual <= score < umbral_fusion_automatica (85-97.99%) -> REVISION_MANUAL
    score < umbral_revision_manual (< 85%)                  -> MANTENER_SEPARADAS

Pura: solo clasifica un score segun umbrales configurables. Quien ejecuta
la fusion, crea el caso de revision, o no hace nada es `FusionService`
(application) -- este modulo nunca toca un repositorio.
"""

from __future__ import annotations

from govdata.domain.rules.reglas_identidad import UmbralesFusion
from govdata.domain.value_objects.decision_fusion import DecisionFusion


def decidir_fusion(score: float, umbrales: UmbralesFusion) -> DecisionFusion:
    if score >= umbrales.umbral_fusion_automatica:
        return DecisionFusion.FUSION_AUTOMATICA
    if score >= umbrales.umbral_revision_manual:
        return DecisionFusion.REVISION_MANUAL
    return DecisionFusion.MANTENER_SEPARADAS
