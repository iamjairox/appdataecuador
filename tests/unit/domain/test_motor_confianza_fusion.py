"""Tests: Motor de Confianza y Revision Manual (Submodulo 6.21)."""

from __future__ import annotations

from govdata.domain.rules.motor_confianza_fusion import decidir_fusion
from govdata.domain.rules.reglas_identidad import UmbralesFusion
from govdata.domain.value_objects.decision_fusion import DecisionFusion

_UMBRALES = UmbralesFusion(umbral_fusion_automatica=98.0, umbral_revision_manual=85.0)


class TestDecidirFusion:
    def test_score_98_o_mas_es_fusion_automatica(self) -> None:
        assert decidir_fusion(98.0, _UMBRALES) == DecisionFusion.FUSION_AUTOMATICA
        assert decidir_fusion(100.0, _UMBRALES) == DecisionFusion.FUSION_AUTOMATICA

    def test_score_entre_85_y_9799_es_revision_manual(self) -> None:
        assert decidir_fusion(85.0, _UMBRALES) == DecisionFusion.REVISION_MANUAL
        assert decidir_fusion(97.99, _UMBRALES) == DecisionFusion.REVISION_MANUAL
        assert decidir_fusion(90.0, _UMBRALES) == DecisionFusion.REVISION_MANUAL

    def test_score_menor_a_85_mantiene_separadas(self) -> None:
        assert decidir_fusion(84.99, _UMBRALES) == DecisionFusion.MANTENER_SEPARADAS
        assert decidir_fusion(0.0, _UMBRALES) == DecisionFusion.MANTENER_SEPARADAS
