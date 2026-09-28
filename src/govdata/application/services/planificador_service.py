"""Servicio: PlanificadorService -- Submodulos 9.2/9.3 (Planificador)."""

from __future__ import annotations

from govdata.domain.entities.plan_ejecucion import PlanEjecucion
from govdata.domain.rules.planificador import construir_plan
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline


class PlanificadorService:
    def construir_plan_completo(self) -> PlanEjecucion:
        return construir_plan(None)

    def construir_plan_parcial(self, pasos: frozenset[TipoPasoPipeline]) -> PlanEjecucion:
        """Submodulo 9.9 (Pipeline parcial): "Solo Transparencia", "Solo
        SENESCYT", "Solo Foro", "Solo Comparacion", "Solo Perfil"."""
        return construir_plan(pasos)
