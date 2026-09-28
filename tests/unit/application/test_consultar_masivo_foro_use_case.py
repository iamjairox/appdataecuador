"""Tests: ConsultarMasivoForoUseCase (Submodulo 8.13)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.services.alerta_foro_service import AlertaForoService
from govdata.application.services.cache_foro_service import CacheForoService
from govdata.application.services.comparacion_foro_service import ComparacionForoService
from govdata.application.services.consulta_foro_service import ConsultaForoService
from govdata.application.services.enriquecimiento_foro_service import EnriquecimientoForoService
from govdata.application.services.evento_foro_service import EventoForoService
from govdata.application.services.job_manager_service import JobManagerService
from govdata.application.services.registro_foro_service import RegistroForoService
from govdata.application.use_cases.consultar_masivo_foro_use_case import ConsultarMasivoForoUseCase
from govdata.config.rule_engine_foro import cargar_rule_engine_foro
from govdata.domain.entities.persona import Persona
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import ConsultaForoFallidaError
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_extraccion import FakeJobRepository, FakePersonaRepository
from tests.unit.application.fakes_modulo6 import FakePersonaMasterRepository
from tests.unit.application.fakes_modulo8 import (
    FakeAlertaForoRepository,
    FakeConsultaForoRepository,
    FakeEventoForoRepository,
    FakeForoAbogadosPort,
    FakeHistorialForoRepository,
    FakeRegistroForoRepository,
    FakeRegistroForoVersionRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_RULE_ENGINE_FORO = cargar_rule_engine_foro()


def _pm(persona_id: int) -> PersonaMaster:
    return PersonaMaster(persona_id=persona_id, nombre_completo=NombreCompleto("Juan", f"Perez{persona_id}"))


def _caso_uso(foro: FakeForoAbogadosPort):
    pm_repo = FakePersonaMasterRepository()
    persona_repo = FakePersonaRepository()
    consulta_repo = FakeConsultaForoRepository()
    registro_repo = FakeRegistroForoRepository()
    version_repo = FakeRegistroForoVersionRepository()
    historial_repo = FakeHistorialForoRepository()
    alerta_repo = FakeAlertaForoRepository()
    evento_repo = FakeEventoForoRepository()

    enriquecimiento_service = EnriquecimientoForoService(
        cache_service=CacheForoService(consulta_repo, _RULE_ENGINE_FORO.cache),
        foro_port=foro,
        consulta_service=ConsultaForoService(consulta_repo, ahora_provider=lambda: _AHORA),
        comparacion_service=ComparacionForoService(registro_repo),
        registro_service=RegistroForoService(registro_repo, version_repo, historial_repo),
        alerta_service=AlertaForoService(alerta_repo),
        evento_service=EventoForoService(evento_repo),
        rule_engine_foro=_RULE_ENGINE_FORO,
        ahora_provider=lambda: _AHORA,
    )

    job_manager = JobManagerService(FakeJobRepository())
    caso_uso = ConsultarMasivoForoUseCase(pm_repo, persona_repo, enriquecimiento_service, job_manager)
    return caso_uso, pm_repo, persona_repo


class TestEjecutar:
    def test_procesa_todas_las_personas_master_activas(self) -> None:
        foro = FakeForoAbogadosPort([[RegistroForoDTO(registro="R1")], [RegistroForoDTO(registro="R2")]])
        caso_uso, pm_repo, persona_repo = _caso_uso(foro)
        pm1 = pm_repo.guardar(_pm(1))
        pm2 = pm_repo.guardar(_pm(2))
        # `guardar()` solo auto-asigna id cuando viene None -- aqui se
        # necesita un id EXACTO (el `persona_id` de la PersonaMaster), asi
        # que se agrega directo a la lista interna del fake.
        persona_repo.guardadas.append(Persona(id=pm1.persona_id, nombre_completo=NombreCompleto("Juan", "Perez1")))
        persona_repo.guardadas.append(Persona(id=pm2.persona_id, nombre_completo=NombreCompleto("Juan", "Perez2")))

        resultados = caso_uso.ejecutar()
        assert len(resultados) == 2
        assert foro.llamadas == 2

    def test_item_que_falla_no_bloquea_a_los_demas(self) -> None:
        foro = FakeForoAbogadosPort(error=ConsultaForoFallidaError("timeout"))
        caso_uso, pm_repo, persona_repo = _caso_uso(foro)
        pm1 = pm_repo.guardar(_pm(1))
        pm2 = pm_repo.guardar(_pm(2))
        persona_repo.guardadas.append(Persona(id=pm1.persona_id, nombre_completo=NombreCompleto("Juan", "Perez1")))
        persona_repo.guardadas.append(Persona(id=pm2.persona_id, nombre_completo=NombreCompleto("Juan", "Perez2")))

        resultados = caso_uso.ejecutar()
        assert len(resultados) == 2
        assert all(r.error == "timeout" for r in resultados)

    def test_persona_de_origen_no_encontrada_se_omite_sin_bloquear(self) -> None:
        foro = FakeForoAbogadosPort([[RegistroForoDTO(registro="R1")]])
        caso_uso, pm_repo, _persona_repo = _caso_uso(foro)
        pm_repo.guardar(_pm(99))  # sin Persona correspondiente

        resultados = caso_uso.ejecutar()
        assert resultados == []
