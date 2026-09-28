"""Servicio: ComparacionAcademicaService -- orquesta el Comparador
Academico (Submodulo 7.7): obtiene los titulos VIGENTES ya persistidos
para una PersonaMaster, los traduce de vuelta a `PersonaAcademicaDTO`, y
delega la comparacion en si al motor de dominio puro."""

from __future__ import annotations

from govdata.application.dto.diferencia_titulo_dto import DiferenciaTituloDTO
from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.application.ports.titulo_academico_repository_port import (
    TituloAcademicoRepositoryPort,
)
from govdata.domain.rules.comparador_academico import comparar_titulos
from govdata.domain.rules.convertir_titulo_academico import titulo_academico_a_dto


class ComparacionAcademicaService:
    def __init__(self, titulo_repository: TituloAcademicoRepositoryPort) -> None:
        self._titulo_repository = titulo_repository

    def comparar(self, persona_master_id: int, actuales: list[PersonaAcademicaDTO]) -> list[DiferenciaTituloDTO]:
        vigentes = self._titulo_repository.listar_vigentes_por_persona_master(persona_master_id)
        anteriores = [titulo_academico_a_dto(t) for t in vigentes]
        return comparar_titulos(anteriores, actuales)
