"""Tests: MotorPoliticasService + MotorPrioridadesOrquestadorService +
PlanificadorService -- wrappers finos sobre las reglas de dominio puras."""

from __future__ import annotations

import pytest

from govdata.application.services.motor_politicas_service import MotorPoliticasService
from govdata.application.services.motor_prioridades_orquestador_service import (
    MotorPrioridadesOrquestadorService,
)
from govdata.application.services.planificador_service import PlanificadorService
from govdata.domain.exceptions.domain_exceptions import PoliticaEjecucionInvalidaError
from govdata.domain.rules.motor_prioridades_orquestador import SenalesPrioridad
from govdata.domain.rules.reglas_orquestador import (
    CatalogoPoliticas,
    PoliticaEjecucion,
    ReglasPrioridadEjecucion,
)
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline


class TestMotorPoliticasService:
    def test_resuelve_y_lista_politicas(self) -> None:
        catalogo = CatalogoPoliticas(politicas_por_nombre={"consulta_rapida": PoliticaEjecucion(nombre="consulta_rapida")})
        servicio = MotorPoliticasService(catalogo)
        assert servicio.resolver("consulta_rapida").nombre == "consulta_rapida"
        assert servicio.listar_disponibles() == ["consulta_rapida"]

    def test_politica_inexistente_lanza_error(self) -> None:
        servicio = MotorPoliticasService(CatalogoPoliticas())
        with pytest.raises(PoliticaEjecucionInvalidaError):
            servicio.resolver("no_existe")


class TestMotorPrioridadesOrquestadorService:
    def test_calcula_nivel_y_score(self) -> None:
        servicio = MotorPrioridadesOrquestadorService(ReglasPrioridadEjecucion())
        senales = SenalesPrioridad()
        assert servicio.calcular(senales) == NivelPrioridadEjecucion.BAJA
        assert servicio.score(senales) == 0.0


class TestPlanificadorService:
    def test_plan_completo(self) -> None:
        servicio = PlanificadorService()
        plan = servicio.construir_plan_completo()
        assert len(plan.pasos_a_intentar) == 8

    def test_plan_parcial(self) -> None:
        servicio = PlanificadorService()
        plan = servicio.construir_plan_parcial(frozenset({TipoPasoPipeline.FORO}))
        assert plan.paso_incluido(TipoPasoPipeline.FORO)
        assert not plan.paso_incluido(TipoPasoPipeline.SENESCYT)
