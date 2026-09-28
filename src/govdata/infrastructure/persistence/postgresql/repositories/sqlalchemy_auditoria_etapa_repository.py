"""Adaptador: SqlAlchemyAuditoriaEtapaRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.auditoria_etapa_repository_port import AuditoriaEtapaRepositoryPort
from govdata.domain.entities.auditoria_etapa import AuditoriaEtapa
from govdata.infrastructure.persistence.postgresql.mappers import auditoria_etapa_mapper
from govdata.infrastructure.persistence.postgresql.models.auditoria_etapa_model import (
    AuditoriaEtapaModel,
)


class SqlAlchemyAuditoriaEtapaRepository(AuditoriaEtapaRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar_lote(self, etapas: list[AuditoriaEtapa]) -> list[AuditoriaEtapa]:
        guardadas = []
        for etapa in etapas:
            modelo = auditoria_etapa_mapper.a_modelo(etapa)
            self._session.add(modelo)
            guardadas.append(modelo)
        self._session.flush()
        return [auditoria_etapa_mapper.a_dominio(m) for m in guardadas]

    def listar_por_trabajo(self, trabajo_orquestador_id: str) -> list[AuditoriaEtapa]:
        modelos = self._session.execute(
            select(AuditoriaEtapaModel).where(
                AuditoriaEtapaModel.trabajo_orquestador_id == uuid.UUID(trabajo_orquestador_id)
            )
        ).scalars().all()
        return [auditoria_etapa_mapper.a_dominio(m) for m in modelos]

    def listar_todo(self, limite: int = 5000) -> list[AuditoriaEtapa]:
        modelos = self._session.execute(select(AuditoriaEtapaModel).limit(limite)).scalars().all()
        return [auditoria_etapa_mapper.a_dominio(m) for m in modelos]
