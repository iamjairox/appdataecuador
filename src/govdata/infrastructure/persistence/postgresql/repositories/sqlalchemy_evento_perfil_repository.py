"""Adaptador: SqlAlchemyEventoPerfilRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.evento_perfil_repository_port import EventoPerfilRepositoryPort
from govdata.domain.entities.evento_perfil import EventoPerfil
from govdata.domain.value_objects.estado_evento_perfil import EstadoEventoPerfil
from govdata.infrastructure.persistence.postgresql.mappers import evento_perfil_mapper
from govdata.infrastructure.persistence.postgresql.models.evento_perfil_model import (
    EventoPerfilModel,
)


class SqlAlchemyEventoPerfilRepository(EventoPerfilRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, evento: EventoPerfil) -> EventoPerfil:
        modelo_existente = self._session.get(EventoPerfilModel, evento.id)
        modelo = evento_perfil_mapper.a_modelo(evento, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return evento_perfil_mapper.a_dominio(modelo)

    def guardar_lote(self, eventos: list[EventoPerfil]) -> list[EventoPerfil]:
        return [self.guardar(e) for e in eventos]

    def buscar_por_id(self, evento_id: uuid.UUID) -> EventoPerfil | None:
        modelo = self._session.get(EventoPerfilModel, evento_id)
        return evento_perfil_mapper.a_dominio(modelo) if modelo else None

    def listar_pendientes(self, limite: int = 100) -> list[EventoPerfil]:
        modelos = self._session.execute(
            select(EventoPerfilModel).where(EventoPerfilModel.estado == EstadoEventoPerfil.PENDIENTE).limit(limite)
        ).scalars().all()
        return [evento_perfil_mapper.a_dominio(m) for m in modelos]

    def listar_por_persona_master(self, persona_master_id: int) -> list[EventoPerfil]:
        modelos = self._session.execute(
            select(EventoPerfilModel).where(EventoPerfilModel.persona_master_id == persona_master_id)
        ).scalars().all()
        return [evento_perfil_mapper.a_dominio(m) for m in modelos]
