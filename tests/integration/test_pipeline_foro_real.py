"""Test de integracion end-to-end del Modulo 8 contra SQLite real:

    Persona (Modulo 1) -> Resolver Persona Master (Modulo 6, reutilizado)
    -> Consultar SENESCYT (Modulo 7, reutilizado) -> Obtener Cedula ->
    Consultar Foro (fake) -> Normalizar -> Comparar -> Guardar version ->
    Alertas -> Eventos -> Perfil Consolidado (8.10)

Mismo espiritu que `test_pipeline_academico_real.py` (Modulo 7): ejercita
el pipeline completo con persistencia real, incluyendo un ciclo de VARIAS
consultas (para probar versionado/historial real, no solo la primera)."""

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
from govdata.application.services.perfil_academico_service import PerfilAcademicoService
from govdata.application.services.perfil_consolidado_service import PerfilConsolidadoService
from govdata.application.services.registro_foro_service import RegistroForoService
from govdata.application.services.titulo_academico_service import TituloAcademicoService
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.rule_engine_academico import cargar_rule_engine_academico
from govdata.config.rule_engine_foro import cargar_rule_engine_foro
from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.domain.entities.persona import Persona
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.mappers import persona_mapper
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_academica_repository import (
    SqlAlchemyAlertaAcademicaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_foro_repository import (
    SqlAlchemyAlertaForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_caso_revision_identidad_repository import (
    SqlAlchemyCasoRevisionIdentidadRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_consulta_foro_repository import (
    SqlAlchemyConsultaForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_consulta_senescyt_repository import (
    SqlAlchemyConsultaSenescytRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_entidad_repository import (
    SqlAlchemyEntidadRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_academico_repository import (
    SqlAlchemyEventoAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_foro_repository import (
    SqlAlchemyEventoForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_perfil_repository import (
    SqlAlchemyEventoPerfilRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_repository import (
    SqlAlchemyFuncionarioRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_historial_academico_repository import (
    SqlAlchemyHistorialAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_historial_foro_repository import (
    SqlAlchemyHistorialForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
    SqlAlchemyPersonaMasterRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_registro_foro_repository import (
    SqlAlchemyRegistroForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_registro_foro_version_repository import (
    SqlAlchemyRegistroForoVersionRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_titulo_academico_repository import (
    SqlAlchemyTituloAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_titulo_version_academica_repository import (
    SqlAlchemyTituloVersionAcademicaRepository,
)
from tests.unit.application.fakes_modulo7 import FakeSenescytPort
from tests.unit.application.fakes_modulo8 import FakeForoAbogadosPort

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_RULE_ENGINE_IDENTIDAD = cargar_rule_engine_identidad()
_RULE_ENGINE_ACADEMICO = cargar_rule_engine_academico()
_RULE_ENGINE_FORO = cargar_rule_engine_foro()


def _crear_persona_real(sesion, nombres: str, apellidos: str, cedula: str) -> Persona:
    persona = Persona(
        nombre_completo=NombreCompleto(nombres, apellidos), cedula=cedula,
        fingerprint=f"{nombres.upper()}{apellidos.upper()}".replace(" ", ""),
    )
    modelo = persona_mapper.a_modelo(persona)
    sesion.add(modelo)
    sesion.flush()
    return persona_mapper.a_dominio(modelo)


def _armar_pipeline(sesion, senescyt: FakeSenescytPort, foro: FakeForoAbogadosPort):
    pm_repo = SqlAlchemyPersonaMasterRepository(sesion)
    caso_repo = SqlAlchemyCasoRevisionIdentidadRepository(sesion)
    evento_perfil_repo = SqlAlchemyEventoPerfilRepository(sesion)
    identity_service = IdentityResolutionService(pm_repo, _RULE_ENGINE_IDENTIDAD.scoring)
    fusion_service = FusionService(
        pm_repo, caso_repo, evento_perfil_repo, _RULE_ENGINE_IDENTIDAD.fusion, ahora_provider=lambda: _AHORA
    )
    resolver_uc = ResolverOCrearPersonaMasterUseCase(pm_repo, identity_service, fusion_service, ahora_provider=lambda: _AHORA)

    consulta_senescyt_repo = SqlAlchemyConsultaSenescytRepository(sesion)
    titulo_repo = SqlAlchemyTituloAcademicoRepository(sesion)
    version_academica_repo = SqlAlchemyTituloVersionAcademicaRepository(sesion)
    historial_academico_repo = SqlAlchemyHistorialAcademicoRepository(sesion)
    alerta_academica_repo = SqlAlchemyAlertaAcademicaRepository(sesion)
    evento_academico_repo = SqlAlchemyEventoAcademicoRepository(sesion)

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

    consulta_foro_repo = SqlAlchemyConsultaForoRepository(sesion)
    registro_foro_repo = SqlAlchemyRegistroForoRepository(sesion)
    version_foro_repo = SqlAlchemyRegistroForoVersionRepository(sesion)
    historial_foro_repo = SqlAlchemyHistorialForoRepository(sesion)
    alerta_foro_repo = SqlAlchemyAlertaForoRepository(sesion)
    evento_foro_repo = SqlAlchemyEventoForoRepository(sesion)

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

    perfil_consolidado_service = PerfilConsolidadoService(
        pm_repo, SqlAlchemyPersonaRepository(sesion), SqlAlchemyFuncionarioRepository(sesion),
        SqlAlchemyEntidadRepository(sesion), perfil_academico_service, registro_foro_repo, historial_foro_repo,
        evento_foro_repo, alerta_foro_repo,
    )

    return resolver_uc, enriquecimiento_academico_service, enriquecimiento_foro_service, perfil_consolidado_service


class TestPipelineForoCompleto:
    def test_enriquecer_y_construir_perfil_consolidado_end_to_end(self, sesion) -> None:
        senescyt = FakeSenescytPort(
            [[PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1")]]
        )
        foro = FakeForoAbogadosPort([[RegistroForoDTO(registro="F1", provincia="Pichincha", estado="Vigente")]])
        resolver_uc, enriq_academico, enriq_foro, perfil_service = _armar_pipeline(sesion, senescyt, foro)

        persona = _crear_persona_real(sesion, "Juan", "Perez", cedula="0999999999")
        persona_master = resolver_uc.ejecutar(persona)
        sesion.flush()

        from govdata.application.services.identity_resolution_service import (
            senales_desde_persona_master,
        )

        senales = senales_desde_persona_master(persona_master)
        resultado_academico = enriq_academico.enriquecer(persona_master, senales)
        resultado_foro = enriq_foro.enriquecer(persona_master, persona)
        sesion.flush()

        assert resultado_academico.titulos_nuevos == 1
        assert resultado_foro.registros_nuevos == 1

        perfil = perfil_service.construir_perfil(persona_master.id)
        assert perfil.persona["cedula"] == "0999999999"
        assert len(perfil.senescyt["titulos"]) == 1
        assert len(perfil.foro["registros"]) == 1

    def test_ciclo_de_tres_consultas_versiona_correctamente(self, sesion) -> None:
        """Enero: registro nuevo. Febrero: sin cambios. Marzo: cambio de
        provincia -- nunca se pierde el historial de las 3 consultas."""
        v1 = RegistroForoDTO(registro="F1", provincia="Pichincha", estado="Vigente")
        v2 = RegistroForoDTO(registro="F1", provincia="Pichincha", estado="Vigente")
        v3 = RegistroForoDTO(registro="F1", provincia="Guayas", estado="Vigente")
        foro = FakeForoAbogadosPort([[v1], [v2], [v3]])
        resolver_uc, _enriq_academico, enriq_foro, perfil_service = _armar_pipeline(sesion, FakeSenescytPort([[]]), foro)

        persona = _crear_persona_real(sesion, "Ana", "Gomez", cedula="0988888888")
        persona_master = resolver_uc.ejecutar(persona)
        sesion.flush()

        resultado_1 = enriq_foro.enriquecer(persona_master, persona)
        assert resultado_1.registros_nuevos == 1
        sesion.flush()

        from govdata.infrastructure.persistence.postgresql.models.consulta_foro_model import (
            ConsultaForoModel,
        )

        sesion.query(ConsultaForoModel).delete()
        sesion.flush()

        resultado_2 = enriq_foro.enriquecer(persona_master, persona)
        assert resultado_2.cambios_detectados == 0
        sesion.flush()
        sesion.query(ConsultaForoModel).delete()
        sesion.flush()

        resultado_3 = enriq_foro.enriquecer(persona_master, persona)
        assert resultado_3.cambios_detectados == 1
        assert resultado_3.tipos_cambio == ["cambio_provincia"]

        perfil = perfil_service.construir_perfil(persona_master.id)
        assert len(perfil.foro["registros"]) == 1
        assert perfil.foro["registros"][0]["provincia"] == "GUAYAS"
        assert perfil.foro["registros"][0]["numero_version"] == 2
        # 2 entradas de historial: alta (enero) + cambio de provincia (marzo)
        assert len(perfil.foro["historial"]) == 2
