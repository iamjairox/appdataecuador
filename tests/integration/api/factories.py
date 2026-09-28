"""Helpers de siembra de datos para los tests de integracion del Modulo 10
-- todos via los REPOSITORIOS SQLAlchemy reales de Modulos 1/4/6
(congelados), nunca INSERT crudo."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.persona import Persona
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_entidad_repository import (
    SqlAlchemyEntidadRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_repository import (
    SqlAlchemyFuncionarioRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
    SqlAlchemyPersonaMasterRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def crear_entidad(sesion: Session, nombre: str = "Procuraduria General del Estado", **kwargs: Any) -> Entidad:
    entidad = Entidad(nombre=nombre, url_transparencia=f"https://x.test/{nombre}", portal_origen="dpe", **kwargs)
    return SqlAlchemyEntidadRepository(sesion).guardar_o_actualizar(entidad)


def crear_persona(sesion: Session, nombres: str = "Ana", apellidos: str = "Torres", cedula: str = "0102030405") -> Persona:
    return SqlAlchemyPersonaRepository(sesion).guardar(
        Persona(nombre_completo=NombreCompleto(nombres, apellidos), cedula=cedula)
    )


def crear_funcionario(
    sesion: Session, persona: Persona, entidad: Entidad, cargo: str = "Procurador",
    dependencia: str = "Direccion Juridica", area: AreaRelevante = AreaRelevante.JURIDICA,
) -> Funcionario:
    assert persona.id is not None and entidad.id is not None
    return SqlAlchemyFuncionarioRepository(sesion).guardar(
        Funcionario(persona_id=persona.id, entidad_id=entidad.id, cargo=Cargo(cargo), dependencia=dependencia, area_clasificada=area)
    )


def crear_persona_master(sesion: Session, persona: Persona) -> PersonaMaster:
    assert persona.id is not None
    return SqlAlchemyPersonaMasterRepository(sesion).guardar(
        PersonaMaster(persona_id=persona.id, nombre_completo=persona.nombre_completo, creado_en=_AHORA, actualizado_en=_AHORA)
    )


def crear_funcionario_juridico_completo(
    sesion: Session, entidad: Entidad, **kwargs: Any,
) -> tuple[Persona, Funcionario, PersonaMaster]:
    persona = crear_persona(sesion, **kwargs)
    funcionario = crear_funcionario(sesion, persona, entidad)
    persona_master = crear_persona_master(sesion, persona)
    return persona, funcionario, persona_master
