"""Servicio: PriorizacionService -- Submodulo 6.11 (Motor de Priorizacion).

"No consultar todas las Personas primero." Ordena una cola de
`PersonaMaster` candidatas a enriquecer segun el cargo mas relevante que
ocupa cada una (consultado externamente -- ej. via `Funcionario`, Modulo
4/5 -- y pasado como diccionario para que este servicio no dependa de
ningun repositorio de Modulo 4/5)."""

from __future__ import annotations

from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.rules.motor_priorizacion import ordenar_por_prioridad
from govdata.domain.rules.reglas_identidad import ReglasPriorizacion


class PriorizacionService:
    def __init__(self, reglas: ReglasPriorizacion) -> None:
        self._reglas = reglas

    def priorizar(
        self, candidatos: list[PersonaMaster], cargo_por_persona_master: dict[int, str | None]
    ) -> list[PersonaMaster]:
        def _cargo(pm: PersonaMaster) -> str | None:
            return cargo_por_persona_master.get(pm.id) if pm.id is not None else None

        return ordenar_por_prioridad(candidatos, _cargo, self._reglas)
