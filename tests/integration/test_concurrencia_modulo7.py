"""Test de concurrencia: `EnriquecerPersonaAcademicaUseCase` corriendo en
paralelo para MULTIPLES personas distintas, cada hilo con su propia
`Session` SQLAlchemy -- mismo patron que `test_concurrencia_modulo6.py`."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from sqlalchemy.orm import sessionmaker

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
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.mappers import persona_mapper
from govdata.infrastructure.persistence.postgresql.models.titulo_academico_model import (
    TituloAcademicoModel,
)
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
_CANTIDAD_HILOS = 6


def test_multiples_personas_enriquecidas_en_paralelo_sin_perdida(sqlite_engine_multihilo) -> None:
    Factory = sessionmaker(bind=sqlite_engine_multihilo, future=True)

    def _tarea(indice: int) -> int:
        sesion = Factory()
        try:
            persona = Persona(
                nombre_completo=NombreCompleto(f"Persona{indice}", f"Apellido{indice}"),
                correo=Correo(f"persona{indice}@x.com"), fingerprint=f"PERSONA{indice}APELLIDO{indice}",
            )
            modelo = persona_mapper.a_modelo(persona)
            sesion.add(modelo)
            sesion.flush()
            persona_persistida = persona_mapper.a_dominio(modelo)

            pm_repo = SqlAlchemyPersonaMasterRepository(sesion)
            caso_repo = SqlAlchemyCasoRevisionIdentidadRepository(sesion)
            evento_perfil_repo = SqlAlchemyEventoPerfilRepository(sesion)
            identity_service = IdentityResolutionService(pm_repo, _RULE_ENGINE_IDENTIDAD.scoring)
            fusion_service = FusionService(
                pm_repo, caso_repo, evento_perfil_repo, _RULE_ENGINE_IDENTIDAD.fusion, ahora_provider=lambda: _AHORA
            )
            resolver_uc = ResolverOCrearPersonaMasterUseCase(
                pm_repo, identity_service, fusion_service, ahora_provider=lambda: _AHORA
            )

            consulta_repo = SqlAlchemyConsultaSenescytRepository(sesion)
            titulo_repo = SqlAlchemyTituloAcademicoRepository(sesion)
            version_repo = SqlAlchemyTituloVersionAcademicaRepository(sesion)
            historial_repo = SqlAlchemyHistorialAcademicoRepository(sesion)
            alerta_repo = SqlAlchemyAlertaAcademicaRepository(sesion)
            evento_repo = SqlAlchemyEventoAcademicoRepository(sesion)

            senescyt = FakeSenescytPort(
                [[PersonaAcademicaDTO(
                    titulo=f"Titulo{indice}", nivel="Tercer Nivel", institucion="UCE", numero_registro=f"R{indice}"
                )]]
            )
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

            resultado = caso_uso.ejecutar(persona_persistida)
            sesion.commit()
            assert resultado.titulos_nuevos == 1
            return indice
        finally:
            sesion.close()

    with ThreadPoolExecutor(max_workers=_CANTIDAD_HILOS) as executor:
        futuros = [executor.submit(_tarea, i) for i in range(_CANTIDAD_HILOS)]
        resultados = [f.result() for f in as_completed(futuros)]

    assert sorted(resultados) == list(range(_CANTIDAD_HILOS))

    sesion_verificacion = Factory()
    try:
        total = sesion_verificacion.query(TituloAcademicoModel).count()
        assert total == _CANTIDAD_HILOS
    finally:
        sesion_verificacion.close()
