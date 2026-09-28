"""Tests: EnriquecerMasivoAcademicoUseCase (Submodulo 7.12)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.application.services.alerta_academica_service import AlertaAcademicaService
from govdata.application.services.cache_senescyt_service import CacheSenescytService
from govdata.application.services.comparacion_academica_service import ComparacionAcademicaService
from govdata.application.services.consulta_senescyt_service import ConsultaSenescytService
from govdata.application.services.enriquecimiento_academico_service import (
    EnriquecimientoAcademicoService,
)
from govdata.application.services.evento_academico_service import EventoAcademicoService
from govdata.application.services.job_manager_service import JobManagerService
from govdata.application.services.titulo_academico_service import TituloAcademicoService
from govdata.application.use_cases.enriquecer_masivo_academico_use_case import (
    EnriquecerMasivoAcademicoUseCase,
)
from govdata.config.rule_engine_academico import cargar_rule_engine_academico
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import ConsultaSenescytFallidaError
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_extraccion import FakeJobRepository
from tests.unit.application.fakes_modulo6 import FakePersonaMasterRepository
from tests.unit.application.fakes_modulo7 import (
    FakeAlertaAcademicaRepository,
    FakeConsultaSenescytRepository,
    FakeEventoAcademicoRepository,
    FakeHistorialAcademicoRepository,
    FakeSenescytPort,
    FakeTituloAcademicoRepository,
    FakeTituloVersionRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_RULE_ENGINE_ACADEMICO = cargar_rule_engine_academico()


def _pm(persona_id: int) -> PersonaMaster:
    return PersonaMaster(persona_id=persona_id, nombre_completo=NombreCompleto("Juan", f"Perez{persona_id}"))


def _caso_uso(senescyt: FakeSenescytPort):
    pm_repo = FakePersonaMasterRepository()
    consulta_repo = FakeConsultaSenescytRepository()
    titulo_repo = FakeTituloAcademicoRepository()
    version_repo = FakeTituloVersionRepository()
    historial_repo = FakeHistorialAcademicoRepository()
    alerta_repo = FakeAlertaAcademicaRepository()
    evento_repo = FakeEventoAcademicoRepository()

    enriquecimiento_service = EnriquecimientoAcademicoService(
        cache_service=CacheSenescytService(consulta_repo, _RULE_ENGINE_ACADEMICO.cache),
        senescyt_port=senescyt,
        consulta_service=ConsultaSenescytService(consulta_repo, ahora_provider=lambda: _AHORA),
        comparacion_service=ComparacionAcademicaService(titulo_repo),
        titulo_service=TituloAcademicoService(titulo_repo, version_repo, historial_repo),
        alerta_service=AlertaAcademicaService(alerta_repo),
        evento_service=EventoAcademicoService(evento_repo),
        rule_engine_academico=_RULE_ENGINE_ACADEMICO,
        ahora_provider=lambda: _AHORA,
    )

    job_manager = JobManagerService(FakeJobRepository())
    caso_uso = EnriquecerMasivoAcademicoUseCase(pm_repo, enriquecimiento_service, job_manager)
    return caso_uso, pm_repo


class TestEjecutar:
    def test_procesa_todas_las_personas_master_activas(self) -> None:
        senescyt = FakeSenescytPort(
            [
                [PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1")],
                [PersonaAcademicaDTO(titulo="Medico", nivel="Tercer Nivel", institucion="PUCE", numero_registro="R2")],
            ]
        )
        caso_uso, pm_repo = _caso_uso(senescyt)
        pm_repo.guardar(_pm(1))
        pm_repo.guardar(_pm(2))

        resultados = caso_uso.ejecutar()
        assert len(resultados) == 2
        assert senescyt.llamadas == 2

    def test_item_que_falla_no_bloquea_a_los_demas(self) -> None:
        senescyt = FakeSenescytPort(error=ConsultaSenescytFallidaError("timeout"))
        caso_uso, pm_repo = _caso_uso(senescyt)
        pm_repo.guardar(_pm(1))
        pm_repo.guardar(_pm(2))

        resultados = caso_uso.ejecutar()
        assert len(resultados) == 2
        assert all(r.error == "timeout" for r in resultados)

    def test_lista_explicita_de_personas_master_ignora_el_repositorio(self) -> None:
        senescyt = FakeSenescytPort([[]])
        caso_uso, pm_repo = _caso_uso(senescyt)
        pm_repo.guardar(_pm(1))
        pm_repo.guardar(_pm(2))
        objetivo = pm_repo.guardar(_pm(3))

        resultados = caso_uso.ejecutar([objetivo])
        assert len(resultados) == 1
        assert resultados[0].persona_master_id == objetivo.id
