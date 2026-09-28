"""Adaptador: SqlAlchemyConsultaForoRepository."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from govdata.application.ports.consulta_foro_repository_port import ConsultaForoRepositoryPort
from govdata.domain.entities.consulta_foro import ConsultaForo
from govdata.infrastructure.persistence.postgresql.mappers import consulta_foro_mapper
from govdata.infrastructure.persistence.postgresql.models.consulta_foro_model import (
    ConsultaForoModel,
)


class SqlAlchemyConsultaForoRepository(ConsultaForoRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, consulta: ConsultaForo) -> ConsultaForo:
        modelo_existente = self._session.get(ConsultaForoModel, consulta.id) if consulta.id else None
        modelo = consulta_foro_mapper.a_modelo(consulta, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return consulta_foro_mapper.a_dominio(modelo)

    def listar_por_persona_master(self, persona_master_id: int) -> list[ConsultaForo]:
        modelos = self._session.execute(
            select(ConsultaForoModel)
            .where(ConsultaForoModel.persona_master_id == persona_master_id)
            .order_by(desc(ConsultaForoModel.iniciado_en))
        ).scalars().all()
        return [consulta_foro_mapper.a_dominio(m) for m in modelos]

    def ultima_consulta(self, persona_master_id: int) -> ConsultaForo | None:
        modelo = self._session.execute(
            select(ConsultaForoModel)
            .where(ConsultaForoModel.persona_master_id == persona_master_id)
            .order_by(desc(ConsultaForoModel.iniciado_en))
            .limit(1)
        ).scalars().first()
        return consulta_foro_mapper.a_dominio(modelo) if modelo else None

    def listar_todas(self, desde: datetime | None = None) -> list[ConsultaForo]:
        consulta = select(ConsultaForoModel)
        if desde is not None:
            consulta = consulta.where(ConsultaForoModel.iniciado_en >= desde)
        modelos = self._session.execute(consulta).scalars().all()
        return [consulta_foro_mapper.a_dominio(m) for m in modelos]
