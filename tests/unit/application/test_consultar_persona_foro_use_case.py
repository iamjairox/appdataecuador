"""Tests: ConsultarPersonaForoUseCase (Submodulo 8.12)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.services.alerta_academica_service import AlertaAcademicaService
from govdata.application.services.alerta_foro_service import AlertaForoService
from govdata.application.services.cache_foro_service import CacheForoService
from govdata.application.services.cache_senescyt_service import CacheSenescytService
from govdata.application.services.comparacion_academica_service import ComparacionAcademicaService
from govdata.application.services.comparacion_foro_service import ComparacionForoService
from govdata.application.services.consulta_foro_service import ConsultaForoService
from govdata.application.services.consulta_senescyt_service import ConsultaSenescytService
from govdata.application.services.enriquecimiento_academico_service import (
    EnriquecimientoAcademicoService,
)
from govdata.application.services.enriquecimiento_foro_service import EnriquecimientoForoService
from govdata.application.services.evento_academico_service import EventoAcademicoService
from govdata.application.services.evento_foro_service import EventoForoService
from govdata.application.services.fusion_service import FusionService
from govdata.application.services.identity_resolution_service import IdentityResolutionService
from govdata.application.services.job_manager_service import JobManagerService
from govdata.application.services.perfil_academico_service import PerfilAcademicoService
from govdata.application.services.perfil_consolidado_service import PerfilConsolidadoService
from govdata.application.services.registro_foro_service import RegistroForoService
from govdata.application.services.titulo_academico_service import TituloAcademicoService
from govdata.application.use_cases.consultar_persona_foro_use_case import (
    ConsultarPersonaForoUseCase,
)
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.rule_engine_academico import cargar_rule_engine_academico
from govdata.config.rule_engine_foro import cargar_rule_engine_foro
from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.domain.entities.persona import Persona
from govdata.domain.rules.reglas_identidad import UmbralesFusion
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes import FakeEntidadRepository
from tests.unit.application.fakes_extraccion import (
    FakeFuncionarioRepositoryExtraccion,
    FakeJobRepository,
    FakePersonaRepository,
)
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
_RULE_ENGINE_ACADEMICO = cargar_rule_engine_academico()
_RULE_ENGINE_FORO = cargar_rule_engine_foro()


def _caso_uso(senescyt: FakeSenescytPort, foro: FakeForoAbogadosPort):
    pm_repo = FakePersonaMasterRepository()
    caso_repo = FakeCasoRevisionIdentidadRepository()
    evento_perfil_repo = FakeEventoPerfilRepository()
    identity_service = IdentityResolutionService(pm_repo, cargar_rule_engine_identidad().scoring)
    fusion_service = FusionService(pm_repo, caso_repo, evento_perfil_repo, UmbralesFusion(98.0, 85.0), ahora_provider=lambda: _AHORA)
    resolver_uc = ResolverOCrearPersonaMasterUseCase(pm_repo, identity_service, fusion_service, ahora_provider=lambda: _AHORA)

    consulta_senescyt_repo = FakeConsultaSenescytRepository()
    titulo_repo = FakeTituloAcademicoRepository()
    version_academica_repo = FakeTituloVersionRepository()
    historial_academico_repo = FakeHistorialAcademicoRepository()
    alerta_academica_repo = FakeAlertaAcademicaRepository()
    evento_academico_repo = FakeEventoAcademicoRepository()

    enriquecimiento_academico_service = EnriquecimientoAcademicoService(
        cache_service=CacheSenescytService(consulta_senescyt_repo, _RULE_ENGINE_ACADEMICO.cache),
        senescyt_port=senescyt,
        consulta_service=ConsultaSenescytService(consulta_senescyt_repo, ahora_provider=lambda: _AHORA),
        comparacion_service=ComparacionAcademicaService(titulo_repo),
        titulo_service=TituloAcademicoService(titulo_repo, version_academica_repo, historial_academico_repo),
        alerta_service=AlertaAcademicaService(alerta_academica_repo),
        evento_service=EventoAcademicoService(evento_academico_repo),
        rule_engine_academico=_RULE_ENGINE_ACADEMICO,
        ahora_provider=lambda: _AHORA,
    )
    perfil_academico_service = PerfilAcademicoService(
        pm_repo, titulo_repo, historial_academico_repo, evento_academico_repo, alerta_academica_repo
    )

    consulta_foro_repo = FakeConsultaForoRepository()
    registro_foro_repo = FakeRegistroForoRepository()
    version_foro_repo = FakeRegistroForoVersionRepository()
    historial_foro_repo = FakeHistorialForoRepository()
    alerta_foro_repo = FakeAlertaForoRepository()
    evento_foro_repo = FakeEventoForoRepository()

    enriquecimiento_foro_service = EnriquecimientoForoService(
        cache_service=CacheForoService(consulta_foro_repo, _RULE_ENGINE_FORO.cache),
        foro_port=foro,
        consulta_service=ConsultaForoService(consulta_foro_repo, ahora_provider=lambda: _AHORA),
        comparacion_service=ComparacionForoService(registro_foro_repo),
        registro_service=RegistroForoService(registro_foro_repo, version_foro_repo, historial_foro_repo),
        alerta_service=AlertaForoService(alerta_foro_repo),
        evento_service=EventoForoService(evento_foro_repo),
        rule_engine_foro=_RULE_ENGINE_FORO,
        ahora_provider=lambda: _AHORA,
    )

    persona_repo = FakePersonaRepository()
    funcionario_repo = FakeFuncionarioRepositoryExtraccion()
    entidad_repo = FakeEntidadRepository()
    perfil_consolidado_service = PerfilConsolidadoService(
        pm_repo, persona_repo, funcionario_repo, entidad_repo, perfil_academico_service, registro_foro_repo,
        historial_foro_repo, evento_foro_repo, alerta_foro_repo,
    )

    job_manager = JobManagerService(FakeJobRepository())
    caso_uso = ConsultarPersonaForoUseCase(
        resolver_persona_master_use_case=resolver_uc,
        enriquecimiento_academico_service=enriquecimiento_academico_service,
        enriquecimiento_foro_service=enriquecimiento_foro_service,
        perfil_academico_service=perfil_academico_service,
        perfil_consolidado_service=perfil_consolidado_service,
        job_manager=job_manager,
    )
    return caso_uso, pm_repo, persona_repo


def _persona() -> Persona:
    return Persona(
        id=1, nombre_completo=NombreCompleto("Juan", "Perez"), cedula="0999999999", fingerprint="JUANPEREZ",
    )


class TestEjecutar:
    def test_construye_el_contrato_oficial_8_16(self) -> None:
        senescyt = FakeSenescytPort(
            [[PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1")]]
        )
        foro = FakeForoAbogadosPort([[RegistroForoDTO(registro="F1", provincia="Pichincha", estado="Vigente")]])
        caso_uso, _pm_repo, _persona_repo = _caso_uso(senescyt, foro)

        resultado = caso_uso.ejecutar(_persona(), entidad_nombre="Procuraduria General del Estado")

        assert resultado.entidad == "Procuraduria General del Estado"
        assert resultado.documento == "0999999999"
        assert len(resultado.senescyt["titulos"]) == 1
        assert len(resultado.foro["registros"]) == 1

    def test_resuelve_persona_master_automaticamente(self) -> None:
        senescyt = FakeSenescytPort([[]])
        foro = FakeForoAbogadosPort([[]])
        caso_uso, pm_repo, _persona_repo = _caso_uso(senescyt, foro)
        caso_uso.ejecutar(_persona())
        assert len(pm_repo.guardadas) == 1
