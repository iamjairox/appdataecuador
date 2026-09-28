"""Test de concurrencia: `ResolverOCrearPersonaMasterUseCase` corriendo en
paralelo para MULTIPLES personas distintas, cada hilo con su propia
`Session` SQLAlchemy (nunca compartida entre hilos) contra el mismo
archivo SQLite -- mismo patron que `test_concurrencia_modulo5.py`."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from sqlalchemy.orm import sessionmaker

from govdata.application.services.fusion_service import FusionService
from govdata.application.services.identity_resolution_service import IdentityResolutionService
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.domain.entities.persona import Persona
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.mappers import persona_mapper
from govdata.infrastructure.persistence.postgresql.models.persona_master_model import (
    PersonaMasterModel,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_caso_revision_identidad_repository import (
    SqlAlchemyCasoRevisionIdentidadRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_perfil_repository import (
    SqlAlchemyEventoPerfilRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
    SqlAlchemyPersonaMasterRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_RULE_ENGINE_IDENTIDAD = cargar_rule_engine_identidad()
_CANTIDAD_HILOS = 8


def test_multiples_personas_distintas_resueltas_en_paralelo_sin_duplicar(sqlite_engine_multihilo) -> None:
    Factory = sessionmaker(bind=sqlite_engine_multihilo, future=True)

    def _tarea(indice: int) -> int:
        sesion = Factory()
        try:
            persona = Persona(
                nombre_completo=NombreCompleto(f"Persona{indice}", f"Apellido{indice}"),
                correo=Correo(f"persona{indice}@x.com"),
                fingerprint=f"PERSONA{indice}APELLIDO{indice}",
            )
            modelo = persona_mapper.a_modelo(persona)
            sesion.add(modelo)
            sesion.flush()
            persona_persistida = persona_mapper.a_dominio(modelo)

            pm_repo = SqlAlchemyPersonaMasterRepository(sesion)
            caso_repo = SqlAlchemyCasoRevisionIdentidadRepository(sesion)
            evento_repo = SqlAlchemyEventoPerfilRepository(sesion)
            identity_service = IdentityResolutionService(pm_repo, _RULE_ENGINE_IDENTIDAD.scoring)
            fusion_service = FusionService(
                pm_repo, caso_repo, evento_repo, _RULE_ENGINE_IDENTIDAD.fusion, ahora_provider=lambda: _AHORA
            )
            caso_uso = ResolverOCrearPersonaMasterUseCase(
                pm_repo, identity_service, fusion_service, ahora_provider=lambda: _AHORA
            )

            persona_master = caso_uso.ejecutar(persona_persistida)
            sesion.commit()
            return indice, persona_master.persona_id
        finally:
            sesion.close()

    with ThreadPoolExecutor(max_workers=_CANTIDAD_HILOS) as executor:
        futuros = [executor.submit(_tarea, i) for i in range(_CANTIDAD_HILOS)]
        resultados = [f.result() for f in as_completed(futuros)]

    # cada hilo resolvio exactamente su propia Persona (indice unico) --
    # los ids autoincrementales no se comparan directamente (el orden de
    # insercion entre hilos no es determinista), solo que cada indice
    # aparece una unica vez.
    assert sorted(indice for indice, _persona_id in resultados) == list(range(_CANTIDAD_HILOS))
    assert len({persona_id for _indice, persona_id in resultados}) == _CANTIDAD_HILOS

    sesion_verificacion = Factory()
    try:
        total = sesion_verificacion.query(PersonaMasterModel).count()
        # cada hilo resolvio una Persona con fingerprint UNICO -> cada uno
        # debio crear exactamente una PersonaMaster, sin perdidas ni
        # duplicados por condiciones de carrera entre sesiones.
        assert total == _CANTIDAD_HILOS
    finally:
        sesion_verificacion.close()
