"""Test de integracion end-to-end del Modulo 7 contra SQLite real:

    Persona (Modulo 1-5) -> Resolver Persona Master (Modulo 6, reutilizado)
    -> Consultar SENESCYT (fake) -> Normalizar -> Comparar -> Guardar
    version -> Actualizar Perfil Maestro -> Alertas -> Eventos ->
    Resultado enriquecido -> PerfilAcademicoDTO (7.16)

Mismo espiritu que `test_pipeline_identidad_real.py` (Modulo 6) y
`test_monitoreo_multiples_versiones_real.py` (Modulo 5): ejercita el
pipeline completo con persistencia real, incluyendo un ciclo de VARIAS
consultas (para probar versionado/historial real, no solo la primera).
"""

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
from govdata.application.services.perfil_academico_service import PerfilAcademicoService
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
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.mappers import persona_mapper
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_academica_repository import (
    SqlAlchemyAlertaAcademicaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_caso_revision_identidad_repository import (
    SqlAlchemyCasoRevisionIdentidadRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_consulta_senescyt_repository import (
    SqlAlchemyConsultaSenescytRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_academico_repository import (
    SqlAlchemyEventoAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_perfil_repository import (
    SqlAlchemyEventoPerfilRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_historial_academico_repository import (
    SqlAlchemyHistorialAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_job_repository import (
    SqlAlchemyJobRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
    SqlAlchemyPersonaMasterRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_titulo_academico_repository import (
    SqlAlchemyTituloAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_titulo_version_academica_repository import (
    SqlAlchemyTituloVersionAcademicaRepository,
)
from tests.unit.application.fakes_modulo7 import FakeSenescytPort

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_RULE_ENGINE_IDENTIDAD = cargar_rule_engine_identidad()
_RULE_ENGINE_ACADEMICO = cargar_rule_engine_academico()


def _crear_persona_real(sesion, nombres: str, apellidos: str, correo: str | None = None) -> Persona:
    persona = Persona(
        nombre_completo=NombreCompleto(nombres, apellidos), correo=Correo(correo) if correo else None,
        fingerprint=f"{nombres.upper()}{apellidos.upper()}".replace(" ", ""),
    )
    modelo = persona_mapper.a_modelo(persona)
    sesion.add(modelo)
    sesion.flush()
    return persona_mapper.a_dominio(modelo)


def _armar_caso_uso(sesion, senescyt: FakeSenescytPort):
    pm_repo = SqlAlchemyPersonaMasterRepository(sesion)
    caso_repo = SqlAlchemyCasoRevisionIdentidadRepository(sesion)
    evento_perfil_repo = SqlAlchemyEventoPerfilRepository(sesion)
    identity_service = IdentityResolutionService(pm_repo, _RULE_ENGINE_IDENTIDAD.scoring)
    fusion_service = FusionService(
        pm_repo, caso_repo, evento_perfil_repo, _RULE_ENGINE_IDENTIDAD.fusion, ahora_provider=lambda: _AHORA
    )
    resolver_uc = ResolverOCrearPersonaMasterUseCase(pm_repo, identity_service, fusion_service, ahora_provider=lambda: _AHORA)

    consulta_repo = SqlAlchemyConsultaSenescytRepository(sesion)
    titulo_repo = SqlAlchemyTituloAcademicoRepository(sesion)
    version_repo = SqlAlchemyTituloVersionAcademicaRepository(sesion)
    historial_repo = SqlAlchemyHistorialAcademicoRepository(sesion)
    alerta_repo = SqlAlchemyAlertaAcademicaRepository(sesion)
    evento_repo = SqlAlchemyEventoAcademicoRepository(sesion)

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
    job_manager = JobManagerService(SqlAlchemyJobRepository(sesion))
    caso_uso = EnriquecerPersonaAcademicaUseCase(resolver_uc, enriquecimiento_service, job_manager)

    perfil_service = PerfilAcademicoService(pm_repo, titulo_repo, historial_repo, evento_repo, alerta_repo)
    return caso_uso, perfil_service


class TestPipelineAcademicoCompleto:
    def test_enriquecer_y_construir_perfil_end_to_end(self, sesion) -> None:
        senescyt = FakeSenescytPort(
            [[PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1")]]
        )
        caso_uso, perfil_service = _armar_caso_uso(sesion, senescyt)

        persona = _crear_persona_real(sesion, "Juan", "Perez", correo="juan.perez@dpe.gob.ec")
        resultado = caso_uso.ejecutar(persona)
        sesion.flush()

        assert resultado.titulos_nuevos == 1

        from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
            SqlAlchemyPersonaMasterRepository as _Repo,
        )

        pm = _Repo(sesion).buscar_por_persona_id(persona.id)
        assert pm is not None

        perfil = perfil_service.construir_perfil(pm.id)
        contrato = perfil.to_dict()
        assert len(contrato["titulos"]) == 1
        assert contrato["titulos"][0]["titulo"] == "ABOGADO"
        assert len(contrato["alertas"]) == 1
        assert len(contrato["eventos"]) >= 1

    def test_ciclo_de_tres_consultas_versiona_correctamente(self, sesion) -> None:
        """Enero: titulo nuevo. Febrero: sin cambios (cache fuerza
        omision -- se limpia para forzar la consulta). Marzo: cambio de
        nivel -- nunca se pierde el historial de las 3 consultas."""
        v1 = PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1")
        v2 = PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1")
        v3 = PersonaAcademicaDTO(titulo="Abogado", nivel="Cuarto Nivel", institucion="UCE", numero_registro="R1")
        senescyt = FakeSenescytPort([[v1], [v2], [v3]])
        caso_uso, perfil_service = _armar_caso_uso(sesion, senescyt)

        persona = _crear_persona_real(sesion, "Ana", "Gomez", correo="ana@x.com")

        resultado_1 = caso_uso.ejecutar(persona)
        assert resultado_1.titulos_nuevos == 1
        sesion.flush()

        # Forzar que el cache permita la 2da y 3ra consulta.
        from govdata.infrastructure.persistence.postgresql.models.consulta_senescyt_model import (
            ConsultaSenescytModel,
        )

        sesion.query(ConsultaSenescytModel).delete()
        sesion.flush()

        resultado_2 = caso_uso.ejecutar(persona)
        assert resultado_2.cambios_detectados == 0
        sesion.flush()
        sesion.query(ConsultaSenescytModel).delete()
        sesion.flush()

        resultado_3 = caso_uso.ejecutar(persona)
        assert resultado_3.cambios_detectados == 1
        assert resultado_3.tipos_cambio == ["cambio_nivel"]

        from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
            SqlAlchemyPersonaMasterRepository as _Repo,
        )

        pm = _Repo(sesion).buscar_por_persona_id(persona.id)
        assert pm is not None
        perfil = perfil_service.construir_perfil(pm.id)
        contrato = perfil.to_dict()
        assert len(contrato["titulos"]) == 1
        assert contrato["titulos"][0]["nivel"] == "CUARTO NIVEL"
        assert contrato["titulos"][0]["numero_version"] == 2
        # 2 entradas de historial: alta (enero) + cambio de nivel (marzo)
        assert len(contrato["historial"]) == 2
