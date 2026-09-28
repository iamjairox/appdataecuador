"""Adaptador: SqlAlchemyHistorialForoRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.historial_foro_repository_port import HistorialForoRepositoryPort
from govdata.domain.entities.historial_foro import HistorialForo
from govdata.infrastructure.persistence.postgresql.mappers import historial_foro_mapper
from govdata.infrastructure.persistence.postgresql.models.historial_foro_model import (
    HistorialForoModel,
)


class SqlAlchemyHistorialForoRepository(HistorialForoRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar_lote(self, registros: list[HistorialForo]) -> list[HistorialForo]:
        guardados = []
        for registro in registros:
            modelo = historial_foro_mapper.a_modelo(registro)
            self._session.add(modelo)
            guardados.append(modelo)
        self._session.flush()
        return [historial_foro_mapper.a_dominio(m) for m in guardados]

    def listar_por_persona_master(self, persona_master_id: int) -> list[HistorialForo]:
        modelos = self._session.execute(
            select(HistorialForoModel).where(HistorialForoModel.persona_master_id == persona_master_id)
        ).scalars().all()
        return [historial_foro_mapper.a_dominio(m) for m in modelos]

    def listar_todo(self) -> list[HistorialForo]:
        modelos = self._session.execute(select(HistorialForoModel)).scalars().all()
        return [historial_foro_mapper.a_dominio(m) for m in modelos]
