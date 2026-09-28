"""Caso de uso: ConsultarPorCedulaForoUseCase -- Submodulo 8.12 (Consulta
Individual: `consultar_por_cedula()`).

Resuelve la `Persona` (Modulo 1, congelado) a partir de una cedula y
delega el resto del flujo en `ConsultarPersonaForoUseCase`."""

from __future__ import annotations

from govdata.application.dto.contrato_consulta_funcionario_dto import (
    ContratoConsultaFuncionarioDTO,
)
from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.application.use_cases.consultar_persona_foro_use_case import (
    ConsultarPersonaForoUseCase,
)
from govdata.domain.exceptions.domain_exceptions import PersonaInvalidaError


class ConsultarPorCedulaForoUseCase:
    def __init__(
        self, persona_repository: PersonaRepositoryPort, consultar_persona_use_case: ConsultarPersonaForoUseCase
    ) -> None:
        self._persona_repository = persona_repository
        self._consultar_persona_use_case = consultar_persona_use_case

    def ejecutar(self, cedula: str, entidad_nombre: str = "") -> ContratoConsultaFuncionarioDTO:
        persona = self._persona_repository.buscar_por_cedula(cedula)
        if persona is None:
            raise PersonaInvalidaError(f"No existe una Persona registrada con cedula: {cedula}")
        return self._consultar_persona_use_case.ejecutar(persona, entidad_nombre=entidad_nombre)
