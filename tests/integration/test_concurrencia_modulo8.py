"""Test de concurrencia: `EnriquecimientoForoService` (via el flujo
completo de identidad + Foro) corriendo en paralelo para MULTIPLES
personas distintas, cada hilo con su propia `Session` SQLAlchemy --
mismo patron que `test_concurrencia_modulo7.py`."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from sqlalchemy.orm import sessionmaker

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.services.alerta_foro_service import AlertaForoService
from govdata.application.services.cache_foro_service import CacheForoService
from govdata.application.services.comparacion_foro_service import ComparacionForoService
from govdata.application.services.consulta_foro_service import ConsultaForoService
from govdata.application.services.enriquecimiento_foro_service import EnriquecimientoForoService
from govdata.application.services.evento_foro_service import EventoForoService
from govdata.application.services.fusion_service import FusionService
from govdata.application.services.identity_resolution_service import IdentityResolutionService
from govdata.application.services.registro_foro_service import RegistroForoService
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.rule_engine_foro import cargar_rule_engine_foro
from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.domain.entities.persona import Persona
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.mappers import persona_mapper
from govdata.infrastructure.persistence.postgresql.models.registro_foro_model import (
    RegistroForoModel,
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
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_foro_repository import (
    SqlAlchemyEventoForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_perfil_repository import (
    SqlAlchemyEventoPerfilRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_historial_foro_repository import (
    SqlAlchemyHistorialForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
    SqlAlchemyPersonaMasterRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_registro_foro_repository import (
    SqlAlchemyRegistroForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_registro_foro_version_repository import (
    SqlAlchemyRegistroForoVersionRepository,
)
from tests.unit.application.fakes_modulo8 import FakeForoAbogadosPort

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_RULE_ENGINE_IDENTIDAD = cargar_rule_engine_identidad()
_RULE_ENGINE_FORO = cargar_rule_engine_foro()
_CANTIDAD_HILOS = 6


def test_multiples_personas_consultadas_en_paralelo_sin_perdida(sqlite_engine_multihilo) -> None:
    Factory = sessionmaker(bind=sqlite_engine_multihilo, future=True)

    def _tarea(indice: int) -> int:
        sesion = Factory()
        try:
            persona = Persona(
                nombre_completo=NombreCompleto(f"Persona{indice}", f"Apellido{indice}"),
                cedula=f"099999999{indice}", fingerprint=f"PERSONA{indice}APELLIDO{indice}",
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
            persona_master = resolver_uc.ejecutar(persona_persistida)

            consulta_repo = SqlAlchemyConsultaForoRepository(sesion)
            registro_repo = SqlAlchemyRegistroForoRepository(sesion)
            version_repo = SqlAlchemyRegistroForoVersionRepository(sesion)
            historial_repo = SqlAlchemyHistorialForoRepository(sesion)
            alerta_repo = SqlAlchemyAlertaForoRepository(sesion)
            evento_repo = SqlAlchemyEventoForoRepository(sesion)

            foro = FakeForoAbogadosPort([[RegistroForoDTO(registro=f"R{indice}", provincia="Pichincha")]])
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

            resultado = enriquecimiento_service.enriquecer(persona_master, persona_persistida)
            sesion.commit()
            assert resultado.registros_nuevos == 1
            return indice
        finally:
            sesion.close()

    with ThreadPoolExecutor(max_workers=_CANTIDAD_HILOS) as executor:
        futuros = [executor.submit(_tarea, i) for i in range(_CANTIDAD_HILOS)]
        resultados = [f.result() for f in as_completed(futuros)]

    assert sorted(resultados) == list(range(_CANTIDAD_HILOS))

    sesion_verificacion = Factory()
    try:
        total = sesion_verificacion.query(RegistroForoModel).count()
        assert total == _CANTIDAD_HILOS
    finally:
        sesion_verificacion.close()
