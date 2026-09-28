"""Adaptador: SqlAlchemyEventoRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.evento_repository_port import EventoRepositoryPort
from govdata.domain.entities.evento import EstadoEvento, Evento
from govdata.infrastructure.persistence.postgresql.mappers import evento_mapper
from govdata.infrastructure.persistence.postgresql.models.evento_model import EventoModel


class SqlAlchemyEventoRepository(EventoRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, evento: Evento) -> Evento:
        modelo_existente = self._session.get(EventoModel, evento.id)
        modelo = evento_mapper.a_modelo(evento, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return evento_mapper.a_dominio(modelo)

    def guardar_lote(self, eventos: list[Evento]) -> list[Evento]:
        return [self.guardar(e) for e in eventos]

    def buscar_por_id(self, evento_id: uuid.UUID) -> Evento | None:
        modelo = self._session.get(EventoModel, evento_id)
        return evento_mapper.a_dominio(modelo) if modelo else None

    def listar_pendientes(self, limite: int) -> list[Evento]:
        modelos = (
            self._session.execute(
                select(EventoModel)
                .where(EventoModel.estado == EstadoEvento.PENDIENTE)
                .order_by(EventoModel.creado_en.asc())
                .limit(limite)
            )
            .scalars()
            .all()
        )
        return [evento_mapper.a_dominio(m) for m in modelos]
