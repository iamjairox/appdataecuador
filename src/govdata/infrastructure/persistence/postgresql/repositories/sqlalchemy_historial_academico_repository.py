"""Adaptador: SqlAlchemyHistorialAcademicoRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.historial_academico_repository_port import (
    HistorialAcademicoRepositoryPort,
)
from govdata.domain.entities.historial_academico import HistorialAcademico
from govdata.infrastructure.persistence.postgresql.mappers import historial_academico_mapper
from govdata.infrastructure.persistence.postgresql.models.historial_academico_model import (
    HistorialAcademicoModel,
)


class SqlAlchemyHistorialAcademicoRepository(HistorialAcademicoRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar_lote(self, registros: list[HistorialAcademico]) -> list[HistorialAcademico]:
        guardados = []
        for registro in registros:
            modelo = historial_academico_mapper.a_modelo(registro)
            self._session.add(modelo)
            guardados.append(modelo)
        self._session.flush()
        return [historial_academico_mapper.a_dominio(m) for m in guardados]

    def listar_por_persona_master(self, persona_master_id: int) -> list[HistorialAcademico]:
        modelos = self._session.execute(
            select(HistorialAcademicoModel).where(HistorialAcademicoModel.persona_master_id == persona_master_id)
        ).scalars().all()
        return [historial_academico_mapper.a_dominio(m) for m in modelos]

    def listar_todo(self) -> list[HistorialAcademico]:
        modelos = self._session.execute(select(HistorialAcademicoModel)).scalars().all()
        return [historial_academico_mapper.a_dominio(m) for m in modelos]
