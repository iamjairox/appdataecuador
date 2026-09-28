"""Test de rendimiento del Modulo 7 -- Submodulo 7.19.

Dos angulos, igual que los equivalentes de Modulos 5/6: el Comparador
Academico (dominio puro, sin IO) debe seguir siendo O(n) razonable con
miles de titulos; y el pipeline completo (con IO real via SQLite) debe
procesar un lote de PersonaMaster en un tiempo acotado, sin degradarse.
Sin umbral "oficial" en la especificacion ("cientos de miles de personas"
es la meta de PRODUCCION con PostgreSQL real) -- los limites aqui son
deliberadamente holgados para no volver la suite fragil en CI, mientras
siguen detectando una regresion algoritmica real.
"""

from __future__ import annotations

import time
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
from govdata.application.use_cases.enriquecer_masivo_academico_use_case import (
    EnriquecerMasivoAcademicoUseCase,
)
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.rule_engine_academico import cargar_rule_engine_academico
from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.domain.entities.persona import Persona
from govdata.domain.rules.comparador_academico import comparar_titulos
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


def _titulos_sinteticos(cantidad: int) -> list[PersonaAcademicaDTO]:
    return [
        PersonaAcademicaDTO(titulo=f"Titulo{i:06d}", nivel="Tercer Nivel", institucion="UCE", numero_registro=f"R{i:06d}")
        for i in range(cantidad)
    ]


def test_comparador_academico_no_degrada_con_miles_de_titulos() -> None:
    cantidad = 5_000
    anteriores = _titulos_sinteticos(cantidad)
    actuales = _titulos_sinteticos(cantidad)
    # 10% cambia de nivel
    for i in range(0, cantidad, 10):
        actuales[i] = PersonaAcademicaDTO(
            titulo=f"Titulo{i:06d}", nivel="Cuarto Nivel", institucion="UCE", numero_registro=f"R{i:06d}"
        )

    inicio = time.perf_counter()
    diffs = comparar_titulos(anteriores, actuales)
    duracion = time.perf_counter() - inicio

    assert len(diffs) == cantidad
    assert duracion < 15.0, f"Comparar {cantidad} titulos tardo {duracion:.2f}s (limite: 15s)"


def test_enriquecimiento_masivo_de_cientos_de_personas(sesion) -> None:
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
        persona = Persona(nombre_completo=NombreCompleto(f"Persona{i:04d}", f"Apellido{i:04d}"), fingerprint=f"PERSONA{i:04d}APELLIDO{i:04d}")
        modelo = persona_mapper.a_modelo(persona)
        sesion.add(modelo)
        sesion.flush()
        persona_persistida = persona_mapper.a_dominio(modelo)
        personas_master.append(resolver_uc.ejecutar(persona_persistida))
    sesion.flush()

    consulta_repo = SqlAlchemyConsultaSenescytRepository(sesion)
    titulo_repo = SqlAlchemyTituloAcademicoRepository(sesion)
    version_repo = SqlAlchemyTituloVersionAcademicaRepository(sesion)
    historial_repo = SqlAlchemyHistorialAcademicoRepository(sesion)
    alerta_repo = SqlAlchemyAlertaAcademicaRepository(sesion)
    evento_repo = SqlAlchemyEventoAcademicoRepository(sesion)

    resultados_por_persona = [
        [PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro=f"R{i}")]
        for i in range(cantidad)
    ]
    senescyt = FakeSenescytPort(resultados_por_persona)

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
    caso_uso_masivo = EnriquecerMasivoAcademicoUseCase(pm_repo, enriquecimiento_service, job_manager)

    inicio = time.perf_counter()
    resultados = caso_uso_masivo.ejecutar(personas_master)
    duracion = time.perf_counter() - inicio

    assert len(resultados) == cantidad
    assert all(r.titulos_nuevos == 1 for r in resultados)
    assert duracion < 60.0, f"Enriquecer {cantidad} personas tardo {duracion:.2f}s (limite: 60s)"
