"""Tests: EnriquecerPersonaAcademicaUseCase (Submodulo 7.11)."""

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
from govdata.application.services.fusion_service import FusionService
from govdata.application.services.identity_resolution_service import IdentityResolutionService
from govdata.application.services.job_manager_service import JobManagerService
from govdata.application.services.titulo_academico_service import TituloAcademicoService
from govdata.application.use_cases.enriquecer_persona_academica_use_case import (
    EnriquecerPersonaAcademicaUseCase,
)
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.rule_engine_academico import cargar_rule_engine_academico
from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.domain.entities.persona import Persona
from govdata.domain.rules.reglas_identidad import UmbralesFusion
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_extraccion import FakeJobRepository
from tests.unit.application.fakes_modulo6 import (
    FakeCasoRevisionIdentidadRepository,
    FakeEventoPerfilRepository,
    FakePersonaMasterRepository,
)
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


def _caso_uso(senescyt: FakeSenescytPort):
    pm_repo = FakePersonaMasterRepository()
    caso_repo = FakeCasoRevisionIdentidadRepository()
    evento_perfil_repo = FakeEventoPerfilRepository()
    identity_service = IdentityResolutionService(pm_repo, cargar_rule_engine_identidad().scoring)
    fusion_service = FusionService(pm_repo, caso_repo, evento_perfil_repo, UmbralesFusion(98.0, 85.0), ahora_provider=lambda: _AHORA)
    resolver_uc = ResolverOCrearPersonaMasterUseCase(pm_repo, identity_service, fusion_service, ahora_provider=lambda: _AHORA)

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
    caso_uso = EnriquecerPersonaAcademicaUseCase(resolver_uc, enriquecimiento_service, job_manager)
    return caso_uso, job_manager, pm_repo


def _persona() -> Persona:
    return Persona(
        id=1, nombre_completo=NombreCompleto("Juan", "Perez"), correo=Correo("juan@x.com"), fingerprint="JUANPEREZ",
    )


class TestEjecutar:
    def test_enriquecimiento_exitoso_finaliza_el_job(self) -> None:
        senescyt = FakeSenescytPort(
            [[PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1")]]
        )
        caso_uso, _job_manager, _pm_repo = _caso_uso(senescyt)

        resultado = caso_uso.ejecutar(_persona())

        assert resultado.consultado is True
        assert resultado.titulos_nuevos == 1

    def test_resuelve_persona_master_automaticamente(self) -> None:
        senescyt = FakeSenescytPort([[]])
        caso_uso, _job_manager, pm_repo = _caso_uso(senescyt)
        caso_uso.ejecutar(_persona())
        assert len(pm_repo.guardadas) == 1
