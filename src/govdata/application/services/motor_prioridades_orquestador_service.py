"""Servicio: MotorPrioridadesOrquestadorService -- Submodulo 9.5."""

from __future__ import annotations

from govdata.domain.rules.motor_prioridades_orquestador import (
    SenalesPrioridad,
    calcular_prioridad,
    calcular_score,
)
from govdata.domain.rules.reglas_orquestador import ReglasPrioridadEjecucion
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion


class MotorPrioridadesOrquestadorService:
    def __init__(self, reglas: ReglasPrioridadEjecucion) -> None:
        self._reglas = reglas

    def calcular(self, senales: SenalesPrioridad) -> NivelPrioridadEjecucion:
        return calcular_prioridad(senales, self._reglas)

    def score(self, senales: SenalesPrioridad) -> float:
        return calcular_score(senales, self._reglas)
