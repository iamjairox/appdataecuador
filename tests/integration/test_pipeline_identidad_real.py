"""Test de integracion end-to-end del Modulo 6 contra SQLite real:

    Persona (Modulo 1-5, ya persistida)
    -> ResolverOCrearPersonaMasterUseCase (6.1/6.2/6.21)
    -> EnriquecerPersonaUseCase (6.7, con una fuente externa FALSA --
       SENESCYT/etc. reales no se implementan en este modulo)
    -> PerfilPersonaService (6.4/6.16, contrato oficial)

Ejercita el pipeline completo con persistencia real (no fakes), igual que
`test_monitoreo_multiples_versiones_real.py` (Modulo 5) hizo para su
propio pipeline -- esta es la clase de prueba que en Modulo 5 encontro
bugs reales que los tests unitarios con fakes no detectaron.
"""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.alerta_perfil_service import AlertaPerfilService
from govdata.application.services.auditoria_consulta_fuente_service import (
    AuditoriaConsultaFuenteService,
)
from govdata.application.services.cache_fuente_service import CacheFuenteService
from govdata.application.services.enriquecimiento_service import EnriquecimientoService
from govdata.application.services.evento_perfil_service import EventoPerfilService
from govdata.application.services.fusion_service import FusionService
from govdata.application.services.historial_service import HistorialService
from govdata.application.services.identity_resolution_service import IdentityResolutionService
from govdata.application.services.perfil_persona_service import PerfilPersonaService
from govdata.application.services.registro_fuente_service import RegistroFuenteService
from govdata.application.services.timeline_persona_service import TimelinePersonaService
from govdata.application.use_cases.enriquecer_persona_use_case import EnriquecerPersonaUseCase
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.domain.entities.persona import Persona
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.estado_persona_master import EstadoPersonaMaster
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.mappers import persona_mapper
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_perfil_repository import (
    SqlAlchemyAlertaPerfilRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_atributo_trazable_repository import (
    SqlAlchemyAtributoTrazableRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_caso_revision_identidad_repository import (
    SqlAlchemyCasoRevisionIdentidadRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_consulta_fuente_log_repository import (
    SqlAlchemyConsultaFuenteLogRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_perfil_repository import (
    SqlAlchemyEventoPerfilRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
    SqlAlchemyPersonaMasterRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_registro_fuente_repository import (
    SqlAlchemyRegistroFuenteRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_version_funcionario_repository import (
    SqlAlchemyVersionFuncionarioRepository,
)
from tests.unit.application.fakes_modulo6 import FakeExternalSourcePort

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_RULE_ENGINE_IDENTIDAD = cargar_rule_engine_identidad()


def _crear_persona_real(sesion, nombres: str, apellidos: str, correo: str | None = None) -> Persona:
    persona = Persona(
        nombre_completo=NombreCompleto(nombres, apellidos), correo=Correo(correo) if correo else None,
        fingerprint=f"{nombres.upper()}{apellidos.upper()}".replace(" ", ""),
    )
    modelo = persona_mapper.a_modelo(persona)
    sesion.add(modelo)
    sesion.flush()
    return persona_mapper.a_dominio(modelo)


def _armar_pipeline(sesion):
    pm_repo = SqlAlchemyPersonaMasterRepository(sesion)
    caso_repo = SqlAlchemyCasoRevisionIdentidadRepository(sesion)
    evento_repo = SqlAlchemyEventoPerfilRepository(sesion)
    registro_repo = SqlAlchemyRegistroFuenteRepository(sesion)
    atributo_repo = SqlAlchemyAtributoTrazableRepository(sesion)
    log_repo = SqlAlchemyConsultaFuenteLogRepository(sesion)
    alerta_repo = SqlAlchemyAlertaPerfilRepository(sesion)
    version_repo = SqlAlchemyVersionFuncionarioRepository(sesion)

    identity_service = IdentityResolutionService(pm_repo, _RULE_ENGINE_IDENTIDAD.scoring)
    fusion_service = FusionService(
        pm_repo, caso_repo, evento_repo, _RULE_ENGINE_IDENTIDAD.fusion, ahora_provider=lambda: _AHORA
    )
    resolver_uc = ResolverOCrearPersonaMasterUseCase(pm_repo, identity_service, fusion_service, ahora_provider=lambda: _AHORA)

    enriquecimiento_service = EnriquecimientoService(
        CacheFuenteService(log_repo, _RULE_ENGINE_IDENTIDAD.cache_por_fuente),
        RegistroFuenteService(registro_repo, atributo_repo),
        AuditoriaConsultaFuenteService(log_repo, ahora_provider=lambda: _AHORA),
        AlertaPerfilService(alerta_repo),
        EventoPerfilService(evento_repo),
        pm_repo,
        ahora_provider=lambda: _AHORA,
    )
    enriquecer_uc = EnriquecerPersonaUseCase(enriquecimiento_service)

    historial_service = HistorialService(version_repo)
    timeline_service = TimelinePersonaService(historial_service, registro_repo)
    perfil_service = PerfilPersonaService(
        pm_repo, registro_repo, historial_service, evento_repo, alerta_repo, timeline_service
    )
    return resolver_uc, enriquecer_uc, perfil_service, pm_repo


class TestPipelineCompletoDeIdentidad:
    def test_resolver_enriquecer_y_construir_perfil_end_to_end(self, sesion) -> None:
        resolver_uc, enriquecer_uc, perfil_service, _pm_repo = _armar_pipeline(sesion)

        persona = _crear_persona_real(sesion, "Juan", "Perez", correo="juan.perez@dpe.gob.ec")
        persona_master = resolver_uc.ejecutar(persona, cargo="Asesor Juridico", institucion="DPE")
        assert persona_master.estado == EstadoPersonaMaster.ACTIVA
        sesion.flush()

        fuente = FakeExternalSourcePort(
            FuenteExterna.SENESCYT, datos_por_llamada=[{"titulo": "Abogado", "profesion": "Derecho"}],
            ahora_provider=lambda: _AHORA,
        )
        resultado_enriquecimiento = enriquecer_uc.ejecutar(persona_master, [fuente], cargo="Asesor Juridico", institucion="DPE")
        assert resultado_enriquecimiento.fuentes_consultadas == ["senescyt"]
        sesion.flush()

        perfil = perfil_service.construir_perfil(persona_master.id)
        contrato = perfil.to_dict()
        assert contrato["identidad"]["persona_master_id"] == persona_master.id
        assert "Abogado" in contrato["perfil"]["titulos"]
        assert contrato["estadisticas"]["cantidad_fuentes"] == 2  # DPE (implicita) + SENESCYT

    def test_misma_persona_re_extraida_dos_veces_es_idempotente(self, sesion) -> None:
        """Volver a resolver la MISMA `Persona` (mismo id, ej. una segunda
        corrida del pipeline DPE sobre el mismo registro) nunca crea una
        segunda PersonaMaster -- `buscar_por_persona_id` la encuentra de
        inmediato, sin pasar siquiera por el Motor de Resolucion."""
        resolver_uc, _enriquecer_uc, _perfil_service, pm_repo = _armar_pipeline(sesion)

        persona = _crear_persona_real(sesion, "Ana", "Gomez", correo="ana@x.com")
        pm1 = resolver_uc.ejecutar(persona, cargo="Directora Financiera", institucion="DPE")
        sesion.flush()
        pm2 = resolver_uc.ejecutar(persona, cargo="Directora Financiera", institucion="DPE")
        sesion.flush()

        assert pm1.id == pm2.id
        activas = pm_repo.listar_activas(limite=100)
        assert len(activas) == 1

    def test_dos_personas_distintas_con_fingerprint_y_correo_iguales_van_a_revision_manual(self, sesion) -> None:
        """Dos filas `Persona` DISTINTAS (ej. dos extracciones separadas)
        que comparten fingerprint y correo, pero cuyo cargo/institucion
        del lado de la candidata ya persistida no se conoce (limitacion
        documentada), alcanzan como maximo 90% de score -- el sistema las
        deja como identidades separadas EN_REVISION en vez de arriesgar
        una fusion automatica incorrecta ("nunca fusionar con baja
        confianza")."""
        resolver_uc, _enriquecer_uc, _perfil_service, _pm_repo = _armar_pipeline(sesion)

        persona_1 = _crear_persona_real(sesion, "Ana", "Gomez", correo="ana@x.com")
        persona_2 = _crear_persona_real(sesion, "Ana", "Gomez", correo="ana@x.com")

        pm1 = resolver_uc.ejecutar(persona_1, cargo="Directora Financiera", institucion="DPE")
        sesion.flush()
        pm2 = resolver_uc.ejecutar(persona_2, cargo="Directora Financiera", institucion="DPE")
        sesion.flush()

        assert pm1.id != pm2.id
        assert pm2.estado == EstadoPersonaMaster.EN_REVISION
        casos_pendientes = SqlAlchemyCasoRevisionIdentidadRepository(sesion).listar_pendientes()
        assert len(casos_pendientes) == 1
