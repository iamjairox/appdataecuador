"""Tests: ConsultarEntidadUseCase -- EL FLUJO OBLIGATORIO del Modulo 8
(Submodulo 8.11)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

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
from govdata.application.services.registro_foro_service import RegistroForoService
from govdata.application.services.titulo_academico_service import TituloAcademicoService
from govdata.application.use_cases.consultar_entidad_use_case import ConsultarEntidadUseCase
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.rule_engine_academico import cargar_rule_engine_academico
from govdata.config.rule_engine_foro import cargar_rule_engine_foro
from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import (
    ConsultaForoFallidaError,
    EntidadNoEncontradaError,
)
from govdata.domain.rules.reglas_identidad import UmbralesFusion
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
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


def _entorno(senescyt: FakeSenescytPort, foro: FakeForoAbogadosPort):
    entidad_repo = FakeEntidadRepository()
    funcionario_repo = FakeFuncionarioRepositoryExtraccion()
    persona_repo = FakePersonaRepository()
    registro_foro_repo = FakeRegistroForoRepository()

    pm_repo = FakePersonaMasterRepository()
    caso_repo = FakeCasoRevisionIdentidadRepository()
    evento_perfil_repo = FakeEventoPerfilRepository()
    identity_service = IdentityResolutionService(pm_repo, cargar_rule_engine_identidad().scoring)
    fusion_service = FusionService(pm_repo, caso_repo, evento_perfil_repo, UmbralesFusion(98.0, 85.0), ahora_provider=lambda: _AHORA)
    resolver_uc = ResolverOCrearPersonaMasterUseCase(pm_repo, identity_service, fusion_service, ahora_provider=lambda: _AHORA)

    consulta_senescyt_repo = FakeConsultaSenescytRepository()
    enriquecimiento_academico_service = EnriquecimientoAcademicoService(
        cache_service=CacheSenescytService(consulta_senescyt_repo, _RULE_ENGINE_ACADEMICO.cache),
        senescyt_port=senescyt,
        consulta_service=ConsultaSenescytService(consulta_senescyt_repo, ahora_provider=lambda: _AHORA),
        comparacion_service=ComparacionAcademicaService(FakeTituloAcademicoRepository()),
        titulo_service=TituloAcademicoService(
            FakeTituloAcademicoRepository(), FakeTituloVersionRepository(), FakeHistorialAcademicoRepository()
        ),
        alerta_service=AlertaAcademicaService(FakeAlertaAcademicaRepository()),
        evento_service=EventoAcademicoService(FakeEventoAcademicoRepository()),
        rule_engine_academico=_RULE_ENGINE_ACADEMICO,
        ahora_provider=lambda: _AHORA,
    )

    consulta_foro_repo = FakeConsultaForoRepository()
    version_foro_repo = FakeRegistroForoVersionRepository()
    historial_foro_repo = FakeHistorialForoRepository()
    enriquecimiento_foro_service = EnriquecimientoForoService(
        cache_service=CacheForoService(consulta_foro_repo, _RULE_ENGINE_FORO.cache),
        foro_port=foro,
        consulta_service=ConsultaForoService(consulta_foro_repo, ahora_provider=lambda: _AHORA),
        comparacion_service=ComparacionForoService(registro_foro_repo),
        registro_service=RegistroForoService(registro_foro_repo, version_foro_repo, historial_foro_repo),
        alerta_service=AlertaForoService(FakeAlertaForoRepository()),
        evento_service=EventoForoService(FakeEventoForoRepository()),
        rule_engine_foro=_RULE_ENGINE_FORO,
        ahora_provider=lambda: _AHORA,
    )

    job_manager = JobManagerService(FakeJobRepository())
    caso_uso = ConsultarEntidadUseCase(
        entidad_repository=entidad_repo, funcionario_repository=funcionario_repo, persona_repository=persona_repo,
        registro_foro_repository=registro_foro_repo, resolver_persona_master_use_case=resolver_uc,
        enriquecimiento_academico_service=enriquecimiento_academico_service,
        enriquecimiento_foro_service=enriquecimiento_foro_service, job_manager=job_manager,
    )
    return caso_uso, entidad_repo, funcionario_repo, persona_repo


def _entidad(entidad_repo: FakeEntidadRepository) -> Entidad:
    return entidad_repo.guardar_o_actualizar(
        Entidad(nombre="Procuraduria General del Estado", url_transparencia="https://x.test", portal_origen="dpe")
    )


class TestEjecutar:
    def test_entidad_no_encontrada_lanza_error(self) -> None:
        caso_uso, _entidad_repo, _funcionario_repo, _persona_repo = _entorno(FakeSenescytPort([[]]), FakeForoAbogadosPort([[]]))
        with pytest.raises(EntidadNoEncontradaError):
            caso_uso.ejecutar("Entidad Inexistente")

    def test_filtra_solo_funcionarios_del_area_juridica(self) -> None:
        senescyt = FakeSenescytPort([[PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE")]])
        foro = FakeForoAbogadosPort([[
            RegistroForoDTO(
                registro="R1", provincia="Pichincha", estado="Vigente",
                correo="juan.perez@ejemplo.com", celular="0991234567",
            )
        ]])
        caso_uso, entidad_repo, funcionario_repo, persona_repo = _entorno(senescyt, foro)
        entidad = _entidad(entidad_repo)

        p_juridico = persona_repo.guardar(Persona(nombre_completo=NombreCompleto("Juan", "Perez"), cedula="0999999999"))
        p_financiero = persona_repo.guardar(Persona(nombre_completo=NombreCompleto("Ana", "Gomez"), cedula="0988888888"))
        funcionario_repo.guardar(
            Funcionario(
                persona_id=p_juridico.id, entidad_id=entidad.id, cargo=Cargo("Director Juridico"),
                dependencia="Direccion Juridica", area_clasificada=AreaRelevante.JURIDICA,
            )
        )
        funcionario_repo.guardar(
            Funcionario(
                persona_id=p_financiero.id, entidad_id=entidad.id, cargo=Cargo("Director Financiero"),
                dependencia="Direccion Financiera", area_clasificada=AreaRelevante.FINANCIERA,
            )
        )

        resultado = caso_uso.ejecutar("Procuraduria")

        assert len(resultado.funcionarios) == 1
        assert resultado.funcionarios[0].nombre_completo == "JUAN PEREZ"
        assert resultado.funcionarios[0].cedula == "0999999999"
        assert resultado.funcionarios[0].registro_foro == "R1"
        assert resultado.funcionarios[0].provincia_foro == "PICHINCHA"  # normalizado (8.3)
        assert resultado.funcionarios[0].correo_personal == "juan.perez@ejemplo.com"
        assert resultado.funcionarios[0].celular == "0991234567"
        assert senescyt.llamadas == 1
        assert foro.llamadas == 1

    def test_funcionario_que_falla_no_bloquea_a_los_demas(self) -> None:
        senescyt = FakeSenescytPort([[], []])
        foro = FakeForoAbogadosPort(error=ConsultaForoFallidaError("timeout"))
        caso_uso, entidad_repo, funcionario_repo, persona_repo = _entorno(senescyt, foro)
        entidad = _entidad(entidad_repo)

        p1 = persona_repo.guardar(Persona(nombre_completo=NombreCompleto("Juan", "Perez"), cedula="0999999999"))
        funcionario_repo.guardar(
            Funcionario(
                persona_id=p1.id, entidad_id=entidad.id, cargo=Cargo("Director Juridico"),
                dependencia="Direccion Juridica", area_clasificada=AreaRelevante.JURIDICA,
            )
        )

        # Con el Foro fallando por completo, el flujo no debe lanzar --
        # `EnriquecimientoForoService.enriquecer` captura el GovDataError
        # y retorna un resultado con `error`, no una excepcion.
        resultado = caso_uso.ejecutar("Procuraduria")
        assert len(resultado.funcionarios) == 1  # el registro_foro simplemente queda vacio

    def test_ninguna_persona_del_area_juridica_retorna_lista_vacia(self) -> None:
        caso_uso, entidad_repo, _funcionario_repo, _persona_repo = _entorno(FakeSenescytPort([[]]), FakeForoAbogadosPort([[]]))
        _entidad(entidad_repo)
        resultado = caso_uso.ejecutar("Procuraduria")
        assert resultado.funcionarios == []
