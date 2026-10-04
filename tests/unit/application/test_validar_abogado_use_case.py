"""Tests: ValidarAbogadoUseCase -- mapeo de contacto del Foro a la respuesta."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from govdata.application.dto.identificacion_cedula_dto import CedulaCandidateDTO
from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.ports.consulta_cedula_port import ConsultaCedulaPort
from govdata.application.services.auditoria_consulta_fuente_service import (
    AuditoriaConsultaFuenteService,
)
from govdata.application.services.auditoria_orquestacion_service import AuditoriaOrquestacionService
from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.application.use_cases.validar_abogado_use_case import ValidarAbogadoUseCase
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import GovDataError
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_modulo6 import FakeConsultaFuenteLogRepository
from tests.unit.application.fakes_modulo8 import FakeForoAbogadosPort
from tests.unit.application.fakes_modulo9 import (
    FakeAuditoriaEtapaRepository,
    FakeTrabajoOrquestadorRepository,
)

_AHORA = datetime(2026, 9, 28, tzinfo=UTC)


class _ConsultaCedulaFija(ConsultaCedulaPort):
    def __init__(self, candidatos: list[CedulaCandidateDTO]) -> None:
        self._candidatos = candidatos

    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]:
        return list(self._candidatos)


class _FakePersonaRepository:
    def guardar(self, persona) -> None:
        pass


class _ConsultaCedulaFallbackFija(ConsultaCedulaPort):
    def __init__(self, candidatos: list[CedulaCandidateDTO]) -> None:
        self._candidatos = candidatos

    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]:
        return list(self._candidatos)


class _ConsultaCedulaFallback2Fija(ConsultaCedulaPort):
    def __init__(self, candidatos: list[CedulaCandidateDTO]) -> None:
        self._candidatos = candidatos

    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]:
        return list(self._candidatos)


def _caso(foro: FakeForoAbogadosPort) -> ValidarAbogadoUseCase:
    return ValidarAbogadoUseCase(
        _ConsultaCedulaFija(
            [
                CedulaCandidateDTO(
                    cedula="0999999999",
                    nombres="JUAN",
                    apellido_paterno="PEREZ",
                )
            ]
        ),
        foro,
        AuditoriaConsultaFuenteService(FakeConsultaFuenteLogRepository(), ahora_provider=lambda: _AHORA),
        ColaTrabajosOrquestadorService(FakeTrabajoOrquestadorRepository(), ahora_provider=lambda: _AHORA),
        AuditoriaOrquestacionService(FakeAuditoriaEtapaRepository()),
        _FakePersonaRepository(),
        _ConsultaCedulaFallbackFija(
            [
                CedulaCandidateDTO(
                    cedula="0999999999",
                    nombres="JUAN",
                    apellido_paterno="PEREZ",
                )
            ]
        ),
        _ConsultaCedulaFallback2Fija(
            [
                CedulaCandidateDTO(
                    cedula="0999999999",
                    nombres="JUAN",
                    apellido_paterno="PEREZ",
                )
            ]
        ),
    )


class _ConsultaCedulaFalla(ConsultaCedulaPort):
    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]:
        raise GovDataError("SOURCE_UNAVAILABLE")


class _ConsultaCedulaVacia(ConsultaCedulaPort):
    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]:
        return []


def test_usa_segunda_fuente_si_la_primera_falla() -> None:
    foro = FakeForoAbogadosPort([[]])
    caso = ValidarAbogadoUseCase(
        _ConsultaCedulaFalla(),
        foro,
        AuditoriaConsultaFuenteService(FakeConsultaFuenteLogRepository(), ahora_provider=lambda: _AHORA),
        ColaTrabajosOrquestadorService(FakeTrabajoOrquestadorRepository(), ahora_provider=lambda: _AHORA),
        AuditoriaOrquestacionService(FakeAuditoriaEtapaRepository()),
        _FakePersonaRepository(),
        _ConsultaCedulaFija(
            [CedulaCandidateDTO(cedula="0999999999", nombres="JUAN", apellido_paterno="PEREZ")]
        ),
    )
    persona = Persona(nombre_completo=NombreCompleto("Juan", "Perez"), id=1)
    resultado = asyncio.run(caso.ejecutar(1, persona))
    assert resultado.estado_identificacion == "match_exact"
    assert resultado.cedula == "0999999999"


def test_usa_segunda_fuente_si_la_primera_no_trae_candidatos() -> None:
    foro = FakeForoAbogadosPort([[]])
    caso = ValidarAbogadoUseCase(
        _ConsultaCedulaVacia(),
        foro,
        AuditoriaConsultaFuenteService(FakeConsultaFuenteLogRepository(), ahora_provider=lambda: _AHORA),
        ColaTrabajosOrquestadorService(FakeTrabajoOrquestadorRepository(), ahora_provider=lambda: _AHORA),
        AuditoriaOrquestacionService(FakeAuditoriaEtapaRepository()),
        _FakePersonaRepository(),
        _ConsultaCedulaFija(
            [CedulaCandidateDTO(cedula="0999999999", nombres="JUAN", apellido_paterno="PEREZ")]
        ),
    )
    persona = Persona(nombre_completo=NombreCompleto("Juan", "Perez"), id=1)
    resultado = asyncio.run(caso.ejecutar(1, persona))
    assert resultado.estado_identificacion == "match_exact"
    assert resultado.cedula == "0999999999"


def test_usa_cuarta_fuente_si_las_tres_primeras_fallan() -> None:
    foro = FakeForoAbogadosPort([[]])
    caso = ValidarAbogadoUseCase(
        _ConsultaCedulaFalla(),
        foro,
        AuditoriaConsultaFuenteService(FakeConsultaFuenteLogRepository(), ahora_provider=lambda: _AHORA),
        ColaTrabajosOrquestadorService(FakeTrabajoOrquestadorRepository(), ahora_provider=lambda: _AHORA),
        AuditoriaOrquestacionService(FakeAuditoriaEtapaRepository()),
        _FakePersonaRepository(),
        _ConsultaCedulaFalla(),
        _ConsultaCedulaVacia(),
        _ConsultaCedulaFija(
            [CedulaCandidateDTO(cedula="0999999999", nombres="JUAN", apellido_paterno="PEREZ")]
        ),
    )
    persona = Persona(nombre_completo=NombreCompleto("Juan", "Perez"), id=1)
    resultado = asyncio.run(caso.ejecutar(1, persona))
    assert resultado.estado_identificacion == "match_exact"
    assert resultado.cedula == "0999999999"


def test_propaga_correo_y_celular_del_foro() -> None:
    foro = FakeForoAbogadosPort(
        [
            [
                RegistroForoDTO(
                    registro="REG-1",
                    estado="VIGENTE",
                    provincia="PICHINCHA",
                    correo="jperez@gmail.com",
                    celular="0991234567",
                )
            ]
        ]
    )
    persona = Persona(nombre_completo=NombreCompleto("Juan", "Perez"), id=1)
    resultado = asyncio.run(_caso(foro).ejecutar(1, persona))
    assert resultado.correo_personal == "jperez@gmail.com"
    assert resultado.celular_personal == "0991234567"
    assert resultado.registro_foro == "REG-1"
    assert resultado.estado_foro == "VIGENTE"
    assert resultado.provincia_foro == "PICHINCHA"
    assert resultado.fuente == "foro_abogados"
