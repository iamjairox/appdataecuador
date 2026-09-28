"""Test de rendimiento del Modulo 8 -- Submodulo 8.19.

Dos angulos, igual que los equivalentes de Modulos 5/6/7: el Comparador
Foro (dominio puro, sin IO) debe seguir siendo O(n) razonable con miles
de registros; y la consulta masiva (con IO real via SQLite) debe procesar
un lote de PersonaMaster en un tiempo acotado, sin degradarse. Sin umbral
"oficial" en la especificacion -- los limites aqui son deliberadamente
holgados para no volver la suite fragil en CI, mientras siguen detectando
una regresion algoritmica real."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.services.alerta_foro_service import AlertaForoService
from govdata.application.services.cache_foro_service import CacheForoService
from govdata.application.services.comparacion_foro_service import ComparacionForoService
from govdata.application.services.consulta_foro_service import ConsultaForoService
from govdata.application.services.enriquecimiento_foro_service import EnriquecimientoForoService
from govdata.application.services.evento_foro_service import EventoForoService
from govdata.application.services.fusion_service import FusionService
from govdata.application.services.identity_resolution_service import IdentityResolutionService
from govdata.application.services.job_manager_service import JobManagerService
from govdata.application.services.registro_foro_service import RegistroForoService
from govdata.application.use_cases.consultar_masivo_foro_use_case import ConsultarMasivoForoUseCase
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.rule_engine_foro import cargar_rule_engine_foro
from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.domain.entities.persona import Persona
from govdata.domain.rules.comparador_foro import comparar_registros
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.mappers import persona_mapper
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
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_job_repository import (
    SqlAlchemyJobRepository,
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
from tests.unit.application.fakes_modulo8 import FakeForoAbogadosPort

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_RULE_ENGINE_IDENTIDAD = cargar_rule_engine_identidad()
_RULE_ENGINE_FORO = cargar_rule_engine_foro()


def _registros_sinteticos(cantidad: int) -> list[RegistroForoDTO]:
    return [RegistroForoDTO(registro=f"R{i:06d}", provincia="Pichincha") for i in range(cantidad)]


def test_comparador_foro_no_degrada_con_miles_de_registros() -> None:
    cantidad = 5_000
    anteriores = _registros_sinteticos(cantidad)
    actuales = _registros_sinteticos(cantidad)
    # 10% cambia de provincia
    for i in range(0, cantidad, 10):
        actuales[i] = RegistroForoDTO(registro=f"R{i:06d}", provincia="Guayas")

    inicio = time.perf_counter()
    diffs = comparar_registros(anteriores, actuales)
    duracion = time.perf_counter() - inicio

    assert len(diffs) == cantidad
    assert duracion < 15.0, f"Comparar {cantidad} registros tardo {duracion:.2f}s (limite: 15s)"


def test_consulta_masiva_de_cientos_de_personas(sesion) -> None:
    cantidad = 300

    pm_repo = SqlAlchemyPersonaMasterRepository(sesion)
    caso_repo = SqlAlchemyCasoRevisionIdentidadRepository(sesion)
    evento_perfil_repo = SqlAlchemyEventoPerfilRepository(sesion)
    identity_service = IdentityResolutionService(pm_repo, _RULE_ENGINE_IDENTIDAD.scoring)
    fusion_service = FusionService(
        pm_repo, caso_repo, evento_perfil_repo, _RULE_ENGINE_IDENTIDAD.fusion, ahora_provider=lambda: _AHORA
    )
    resolver_uc = ResolverOCrearPersonaMasterUseCase(pm_repo, identity_service, fusion_service, ahora_provider=lambda: _AHORA)

    personas_master = []
    for i in range(cantidad):
        persona = Persona(
            nombre_completo=NombreCompleto(f"Persona{i:04d}", f"Apellido{i:04d}"),
            fingerprint=f"PERSONA{i:04d}APELLIDO{i:04d}",
        )
        modelo = persona_mapper.a_modelo(persona)
        sesion.add(modelo)
        sesion.flush()
        persona_persistida = persona_mapper.a_dominio(modelo)
        personas_master.append(resolver_uc.ejecutar(persona_persistida))
    sesion.flush()

    consulta_repo = SqlAlchemyConsultaForoRepository(sesion)
    registro_repo = SqlAlchemyRegistroForoRepository(sesion)
    version_repo = SqlAlchemyRegistroForoVersionRepository(sesion)
    historial_repo = SqlAlchemyHistorialForoRepository(sesion)
    alerta_repo = SqlAlchemyAlertaForoRepository(sesion)
    evento_repo = SqlAlchemyEventoForoRepository(sesion)

    resultados_por_persona = [[RegistroForoDTO(registro=f"R{i}")] for i in range(cantidad)]
    foro = FakeForoAbogadosPort(resultados_por_persona)

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
    job_manager = JobManagerService(SqlAlchemyJobRepository(sesion))
    caso_uso_masivo = ConsultarMasivoForoUseCase(
        pm_repo, SqlAlchemyPersonaRepository(sesion), enriquecimiento_service, job_manager
    )

    inicio = time.perf_counter()
    resultados = caso_uso_masivo.ejecutar(personas_master)
    duracion = time.perf_counter() - inicio

    assert len(resultados) == cantidad
    assert all(r.registros_nuevos == 1 for r in resultados)
    assert duracion < 60.0, f"Consultar {cantidad} personas tardo {duracion:.2f}s (limite: 60s)"
