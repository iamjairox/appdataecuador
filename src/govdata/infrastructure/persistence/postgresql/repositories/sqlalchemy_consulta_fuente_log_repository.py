"""Adaptador: SqlAlchemyConsultaFuenteLogRepository."""

from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from govdata.application.ports.consulta_fuente_log_repository_port import (
    ConsultaFuenteLogRepositoryPort,
)
from govdata.domain.entities.consulta_fuente_log import ConsultaFuenteLog
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.infrastructure.persistence.postgresql.mappers import consulta_fuente_log_mapper
from govdata.infrastructure.persistence.postgresql.models.consulta_fuente_log_model import (
    ConsultaFuenteLogModel,
)


class SqlAlchemyConsultaFuenteLogRepository(ConsultaFuenteLogRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, log: ConsultaFuenteLog) -> ConsultaFuenteLog:
        modelo_existente = self._session.get(ConsultaFuenteLogModel, log.id) if log.id else None
        modelo = consulta_fuente_log_mapper.a_modelo(log, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return consulta_fuente_log_mapper.a_dominio(modelo)

    def listar_por_persona_master(self, persona_master_id: int) -> list[ConsultaFuenteLog]:
        modelos = self._session.execute(
            select(ConsultaFuenteLogModel)
            .where(ConsultaFuenteLogModel.persona_master_id == persona_master_id)
            .order_by(desc(ConsultaFuenteLogModel.iniciado_en))
        ).scalars().all()
        return [consulta_fuente_log_mapper.a_dominio(m) for m in modelos]

    def ultima_consulta(self, persona_master_id: int, fuente: FuenteExterna) -> ConsultaFuenteLog | None:
        modelo = self._session.execute(
            select(ConsultaFuenteLogModel)
            .where(
                ConsultaFuenteLogModel.persona_master_id == persona_master_id,
                ConsultaFuenteLogModel.fuente == fuente,
            )
            .order_by(desc(ConsultaFuenteLogModel.iniciado_en))
            .limit(1)
        ).scalars().first()
        return consulta_fuente_log_mapper.a_dominio(modelo) if modelo else None
