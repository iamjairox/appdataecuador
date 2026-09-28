"""Adaptador: SqlAlchemyEventoForoRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.evento_foro_repository_port import EventoForoRepositoryPort
from govdata.domain.entities.evento_foro import EventoForo
from govdata.domain.value_objects.estado_evento_foro import EstadoEventoForo
from govdata.infrastructure.persistence.postgresql.mappers import evento_foro_mapper
from govdata.infrastructure.persistence.postgresql.models.evento_foro_model import EventoForoModel


class SqlAlchemyEventoForoRepository(EventoForoRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, evento: EventoForo) -> EventoForo:
        modelo_existente = self._session.get(EventoForoModel, evento.id)
        modelo = evento_foro_mapper.a_modelo(evento, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return evento_foro_mapper.a_dominio(modelo)

    def guardar_lote(self, eventos: list[EventoForo]) -> list[EventoForo]:
        return [self.guardar(e) for e in eventos]

    def buscar_por_id(self, evento_id: uuid.UUID) -> EventoForo | None:
        modelo = self._session.get(EventoForoModel, evento_id)
        return evento_foro_mapper.a_dominio(modelo) if modelo else None

    def listar_pendientes(self, limite: int = 100) -> list[EventoForo]:
        modelos = self._session.execute(
            select(EventoForoModel).where(EventoForoModel.estado == EstadoEventoForo.PENDIENTE).limit(limite)
        ).scalars().all()
        return [evento_foro_mapper.a_dominio(m) for m in modelos]

    def listar_por_persona_master(self, persona_master_id: int) -> list[EventoForo]:
        modelos = self._session.execute(
            select(EventoForoModel).where(EventoForoModel.persona_master_id == persona_master_id)
        ).scalars().all()
        return [evento_foro_mapper.a_dominio(m) for m in modelos]
