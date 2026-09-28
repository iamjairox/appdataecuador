"""Tests: ConsultarPorCedulaForoUseCase (Submodulo 8.12)."""

from __future__ import annotations

import pytest

from govdata.application.use_cases.consultar_por_cedula_foro_use_case import (
    ConsultarPorCedulaForoUseCase,
)
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import PersonaInvalidaError
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_extraccion import FakePersonaRepository


class _ConsultarPersonaUseCaseFalso:
    def __init__(self) -> None:
        self.llamadas: list[tuple[Persona, str]] = []

    def ejecutar(self, persona: Persona, entidad_nombre: str = "") -> str:
        self.llamadas.append((persona, entidad_nombre))
        return "contrato-simulado"


class TestConsultarPorCedulaForoUseCase:
    def test_resuelve_persona_por_cedula_y_delega(self) -> None:
        persona_repo = FakePersonaRepository()
        persona_repo.guardar(Persona(nombre_completo=NombreCompleto("Juan", "Perez"), cedula="0999999999"))
        delegado = _ConsultarPersonaUseCaseFalso()
        caso_uso = ConsultarPorCedulaForoUseCase(persona_repo, delegado)

        resultado = caso_uso.ejecutar("0999999999", entidad_nombre="Procuraduria")

        assert resultado == "contrato-simulado"
        assert len(delegado.llamadas) == 1
        assert delegado.llamadas[0][0].cedula == "0999999999"
        assert delegado.llamadas[0][1] == "Procuraduria"

    def test_cedula_no_registrada_lanza_error(self) -> None:
        caso_uso = ConsultarPorCedulaForoUseCase(FakePersonaRepository(), _ConsultarPersonaUseCaseFalso())
        with pytest.raises(PersonaInvalidaError):
            caso_uso.ejecutar("0000000000")
