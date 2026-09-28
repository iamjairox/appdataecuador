"""Tests: Planificador -- Submodulos 9.2/9.3/9.9."""

from __future__ import annotations

from govdata.domain.entities.plan_ejecucion import PASOS_EN_ORDEN
from govdata.domain.rules.planificador import construir_plan
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline


class TestConstruirPlan:
    def test_sin_pasos_solicitados_incluye_los_8_pasos(self) -> None:
        plan = construir_plan(None)
        assert len(plan.pasos) == 8
        assert len(plan.pasos_a_intentar) == 8
        assert plan.pasos_omitidos == ()

    def test_todos_los_pasos_del_plan_completo_estan_incluidos(self) -> None:
        # Se recorre PASOS_EN_ORDEN (los 8 pasos del pipeline de entidad),
        # no el enum completo: TipoPasoPipeline tambien incluye etapas de
        # auditoria del Job `validacion_abogado` (IDENTIFICACION,
        # MATCHING_IDENTIDAD, PERSISTENCIA) que no pertenecen a este plan.
        plan = construir_plan(None)
        for tipo in PASOS_EN_ORDEN:
            assert plan.paso_incluido(tipo)

    def test_pipeline_parcial_solo_foro(self) -> None:
        plan = construir_plan(frozenset({TipoPasoPipeline.FORO}))
        assert plan.paso_incluido(TipoPasoPipeline.FORO)
        assert not plan.paso_incluido(TipoPasoPipeline.SENESCYT)
        assert len(plan.pasos_omitidos) == 7
        assert all(p.razon_omision == "pipeline_parcial_no_solicitado" for p in plan.pasos_omitidos)

    def test_pipeline_parcial_solo_perfil(self) -> None:
        plan = construir_plan(frozenset({TipoPasoPipeline.PERFIL}))
        assert plan.paso_incluido(TipoPasoPipeline.PERFIL)
        assert not plan.paso_incluido(TipoPasoPipeline.COMPARACION)
