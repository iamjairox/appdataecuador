"""Adaptador: SqlAlchemyConsultaSenescytRepository."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from govdata.application.ports.consulta_senescyt_repository_port import (
    ConsultaSenescytRepositoryPort,
)
from govdata.domain.entities.consulta_senescyt import ConsultaSenescyt
from govdata.infrastructure.persistence.postgresql.mappers import consulta_senescyt_mapper
from govdata.infrastructure.persistence.postgresql.models.consulta_senescyt_model import (
    ConsultaSenescytModel,
)


class SqlAlchemyConsultaSenescytRepository(ConsultaSenescytRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, consulta: ConsultaSenescyt) -> ConsultaSenescyt:
        modelo_existente = self._session.get(ConsultaSenescytModel, consulta.id) if consulta.id else None
        modelo = consulta_senescyt_mapper.a_modelo(consulta, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return consulta_senescyt_mapper.a_dominio(modelo)

    def listar_por_persona_master(self, persona_master_id: int) -> list[ConsultaSenescyt]:
        modelos = self._session.execute(
            select(ConsultaSenescytModel)
            .where(ConsultaSenescytModel.persona_master_id == persona_master_id)
            .order_by(desc(ConsultaSenescytModel.iniciado_en))
        ).scalars().all()
        return [consulta_senescyt_mapper.a_dominio(m) for m in modelos]

    def ultima_consulta(self, persona_master_id: int) -> ConsultaSenescyt | None:
        modelo = self._session.execute(
            select(ConsultaSenescytModel)
            .where(ConsultaSenescytModel.persona_master_id == persona_master_id)
            .order_by(desc(ConsultaSenescytModel.iniciado_en))
            .limit(1)
        ).scalars().first()
        return consulta_senescyt_mapper.a_dominio(modelo) if modelo else None

    def listar_todas(self, desde: datetime | None = None) -> list[ConsultaSenescyt]:
        consulta = select(ConsultaSenescytModel)
        if desde is not None:
            consulta = consulta.where(ConsultaSenescytModel.iniciado_en >= desde)
        modelos = self._session.execute(consulta).scalars().all()
        return [consulta_senescyt_mapper.a_dominio(m) for m in modelos]
