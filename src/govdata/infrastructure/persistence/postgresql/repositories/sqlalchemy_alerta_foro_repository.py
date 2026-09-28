"""Adaptador: SqlAlchemyAlertaForoRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.alerta_foro_repository_port import AlertaForoRepositoryPort
from govdata.domain.entities.alerta_foro import AlertaForo
from govdata.domain.value_objects.estado_alerta_foro import EstadoAlertaForo
from govdata.infrastructure.persistence.postgresql.mappers import alerta_foro_mapper
from govdata.infrastructure.persistence.postgresql.models.alerta_foro_model import AlertaForoModel


class SqlAlchemyAlertaForoRepository(AlertaForoRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, alerta: AlertaForo) -> AlertaForo:
        modelo_existente = self._session.get(AlertaForoModel, alerta.id)
        modelo = alerta_foro_mapper.a_modelo(alerta, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return alerta_foro_mapper.a_dominio(modelo)

    def guardar_lote(self, alertas: list[AlertaForo]) -> list[AlertaForo]:
        return [self.guardar(a) for a in alertas]

    def buscar_por_id(self, alerta_id: uuid.UUID) -> AlertaForo | None:
        modelo = self._session.get(AlertaForoModel, alerta_id)
        return alerta_foro_mapper.a_dominio(modelo) if modelo else None

    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaForo]:
        modelos = self._session.execute(
            select(AlertaForoModel).where(AlertaForoModel.persona_master_id == persona_master_id)
        ).scalars().all()
        return [alerta_foro_mapper.a_dominio(m) for m in modelos]

    def listar_pendientes(self, limite: int = 100) -> list[AlertaForo]:
        modelos = self._session.execute(
            select(AlertaForoModel).where(AlertaForoModel.estado == EstadoAlertaForo.PENDIENTE).limit(limite)
        ).scalars().all()
        return [alerta_foro_mapper.a_dominio(m) for m in modelos]
