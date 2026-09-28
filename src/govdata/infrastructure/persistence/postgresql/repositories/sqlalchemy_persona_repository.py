"""Adaptador: SqlAlchemyPersonaRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.domain.entities.persona import Persona
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.mappers import persona_mapper
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel


class SqlAlchemyPersonaRepository(PersonaRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, persona: Persona) -> Persona:
        modelo_existente = self._session.get(PersonaModel, persona.id) if persona.id else None
        modelo = persona_mapper.a_modelo(persona, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return persona_mapper.a_dominio(modelo)

    def buscar_por_id(self, persona_id: int) -> Persona | None:
        modelo = self._session.get(PersonaModel, persona_id)
        return persona_mapper.a_dominio(modelo) if modelo else None

    def buscar_por_cedula(self, cedula: str) -> Persona | None:
        modelo = (
            self._session.execute(select(PersonaModel).where(PersonaModel.cedula == cedula))
            .scalars()
            .first()
        )
        return persona_mapper.a_dominio(modelo) if modelo else None

    def buscar_candidatas_por_nombre(self, nombre: NombreCompleto) -> list[Persona]:
        modelos = (
            self._session.execute(
                select(PersonaModel).where(
                    PersonaModel.nombres == nombre.nombres, PersonaModel.apellidos == nombre.apellidos
                )
            )
            .scalars()
            .all()
        )
        return [persona_mapper.a_dominio(m) for m in modelos]

    def buscar_por_fingerprint_hash(self, fingerprint_hash: str) -> Persona | None:
        modelo = (
            self._session.execute(
                select(PersonaModel).where(PersonaModel.fingerprint_hash == fingerprint_hash)
            )
            .scalars()
            .first()
        )
        return persona_mapper.a_dominio(modelo) if modelo else None
