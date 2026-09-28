"""Adaptador: SqlAlchemyEventoAcademicoRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.evento_academico_repository_port import (
    EventoAcademicoRepositoryPort,
)
from govdata.domain.entities.evento_academico import EventoAcademico
from govdata.domain.value_objects.estado_evento_academico import EstadoEventoAcademico
from govdata.infrastructure.persistence.postgresql.mappers import evento_academico_mapper
from govdata.infrastructure.persistence.postgresql.models.evento_academico_model import (
    EventoAcademicoModel,
)


class SqlAlchemyEventoAcademicoRepository(EventoAcademicoRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, evento: EventoAcademico) -> EventoAcademico:
        modelo_existente = self._session.get(EventoAcademicoModel, evento.id)
        modelo = evento_academico_mapper.a_modelo(evento, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return evento_academico_mapper.a_dominio(modelo)

    def guardar_lote(self, eventos: list[EventoAcademico]) -> list[EventoAcademico]:
        return [self.guardar(e) for e in eventos]

    def buscar_por_id(self, evento_id: uuid.UUID) -> EventoAcademico | None:
        modelo = self._session.get(EventoAcademicoModel, evento_id)
        return evento_academico_mapper.a_dominio(modelo) if modelo else None

    def listar_pendientes(self, limite: int = 100) -> list[EventoAcademico]:
        modelos = self._session.execute(
            select(EventoAcademicoModel).where(EventoAcademicoModel.estado == EstadoEventoAcademico.PENDIENTE).limit(limite)
        ).scalars().all()
        return [evento_academico_mapper.a_dominio(m) for m in modelos]

    def listar_por_persona_master(self, persona_master_id: int) -> list[EventoAcademico]:
        modelos = self._session.execute(
            select(EventoAcademicoModel).where(EventoAcademicoModel.persona_master_id == persona_master_id)
        ).scalars().all()
        return [evento_academico_mapper.a_dominio(m) for m in modelos]
