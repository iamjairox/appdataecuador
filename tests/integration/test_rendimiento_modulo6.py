"""Test de rendimiento: el Motor de Identidad debe soportar un universo
GRANDE de `PersonaMaster` sin degradarse -- la clave arquitectonica es que
`IdentityResolutionService.buscar_candidatas` NUNCA escanea toda la tabla
(acota por indice: fingerprint exacto / fonetico / correo), asi que
resolver UNA persona nueva debe tardar aproximadamente lo mismo con 100
PersonaMaster que con miles.

Igual que los equivalentes de Modulos 4/5: sin umbral "oficial" en la
especificacion ("cientos de miles de personas" es la meta de PRODUCCION
con PostgreSQL + indices reales) -- el limite aqui es deliberadamente
holgado para no volver la suite fragil en CI, mientras sigue detectando
una regresion algoritmica real (ej. un `listar_activas` accidental
reemplazando la busqueda indexada)."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.services.identity_resolution_service import IdentityResolutionService
from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
    SqlAlchemyPersonaMasterRepository,
)

_RULE_ENGINE_IDENTIDAD = cargar_rule_engine_identidad()
_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _poblar_personas_master(sesion, cantidad: int) -> None:
    repo = SqlAlchemyPersonaMasterRepository(sesion)
    for i in range(cantidad):
        persona_modelo = PersonaModel(nombres=f"Nombre{i:06d}", apellidos=f"Apellido{i:06d}")
        sesion.add(persona_modelo)
        sesion.flush()
        repo.guardar(
            PersonaMaster(
                persona_id=persona_modelo.id,
                nombre_completo=NombreCompleto(f"Nombre{i:06d}", f"Apellido{i:06d}"),
                fingerprint_principal=f"NOMBRE{i:06d}APELLIDO{i:06d}",
                correo_principal=Correo(f"persona{i:06d}@x.com"),
            )
        )
    sesion.flush()


def test_resolver_identidad_no_degrada_con_miles_de_personas_master(sesion) -> None:
    cantidad = 5_000
    _poblar_personas_master(sesion, cantidad)

    servicio = IdentityResolutionService(SqlAlchemyPersonaMasterRepository(sesion), _RULE_ENGINE_IDENTIDAD.scoring)
    senales_nuevas = SenalesIdentidadDTO(
        nombre="PersonaNueva", apellido="ApellidoNueva", correo="nueva@x.com", fingerprint="PERSONANUEVA_UNICA"
    )

    inicio = time.perf_counter()
    resultado = servicio.resolver(senales_nuevas)
    duracion = time.perf_counter() - inicio

    assert resultado.persona_master_id is None  # ninguna candidata real coincide
    assert duracion < 2.0, f"Resolver identidad tardo {duracion:.3f}s contra {cantidad} PersonaMaster (limite: 2s)"


def test_encontrar_candidata_exacta_entre_miles_es_rapido(sesion) -> None:
    cantidad = 5_000
    _poblar_personas_master(sesion, cantidad)

    objetivo_indice = 2_500
    servicio = IdentityResolutionService(SqlAlchemyPersonaMasterRepository(sesion), _RULE_ENGINE_IDENTIDAD.scoring)
    senales_nuevas = SenalesIdentidadDTO(
        nombre=f"Nombre{objetivo_indice:06d}", apellido=f"Apellido{objetivo_indice:06d}",
        correo=f"persona{objetivo_indice:06d}@x.com", fingerprint=f"NOMBRE{objetivo_indice:06d}APELLIDO{objetivo_indice:06d}",
    )

    inicio = time.perf_counter()
    resultado = servicio.resolver(senales_nuevas)
    duracion = time.perf_counter() - inicio

    assert resultado.persona_master_id is not None
    # fingerprint+correo+nombre+apellido coinciden exactamente (institucion/
    # cargo no se conocen del lado de la candidata ya persistida --
    # limitacion documentada) -> techo de 90% (0.40+0.25+0.15+0.10).
    assert resultado.score == 90.0
    assert duracion < 2.0, f"Encontrar la candidata exacta tardo {duracion:.3f}s (limite: 2s)"


def test_listar_activas_soporta_paginacion_para_procesamiento_por_lotes(sesion) -> None:
    """Submodulo 6.19: streaming/batch processing -- un job masivo de
    enriquecimiento nunca debe cargar el universo completo en memoria."""
    cantidad = 5_000
    _poblar_personas_master(sesion, cantidad)
    repo = SqlAlchemyPersonaMasterRepository(sesion)

    assert repo.contar_activas() == cantidad

    primer_lote = repo.listar_activas(limite=100, offset=0)
    segundo_lote = repo.listar_activas(limite=100, offset=100)
    assert len(primer_lote) == 100
    assert len(segundo_lote) == 100
    assert {p.id for p in primer_lote}.isdisjoint({p.id for p in segundo_lote})
