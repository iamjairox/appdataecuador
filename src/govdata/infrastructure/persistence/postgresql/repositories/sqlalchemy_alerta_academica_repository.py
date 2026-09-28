"""Adaptador: SqlAlchemyAlertaAcademicaRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.alerta_academica_repository_port import (
    AlertaAcademicaRepositoryPort,
)
from govdata.domain.entities.alerta_academica import AlertaAcademica
from govdata.domain.value_objects.estado_alerta_academica import EstadoAlertaAcademica
from govdata.infrastructure.persistence.postgresql.mappers import alerta_academica_mapper
from govdata.infrastructure.persistence.postgresql.models.alerta_academica_model import (
    AlertaAcademicaModel,
)


class SqlAlchemyAlertaAcademicaRepository(AlertaAcademicaRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, alerta: AlertaAcademica) -> AlertaAcademica:
        modelo_existente = self._session.get(AlertaAcademicaModel, alerta.id)
        modelo = alerta_academica_mapper.a_modelo(alerta, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return alerta_academica_mapper.a_dominio(modelo)

    def guardar_lote(self, alertas: list[AlertaAcademica]) -> list[AlertaAcademica]:
        return [self.guardar(a) for a in alertas]

    def buscar_por_id(self, alerta_id: uuid.UUID) -> AlertaAcademica | None:
        modelo = self._session.get(AlertaAcademicaModel, alerta_id)
        return alerta_academica_mapper.a_dominio(modelo) if modelo else None

    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaAcademica]:
        modelos = self._session.execute(
            select(AlertaAcademicaModel).where(AlertaAcademicaModel.persona_master_id == persona_master_id)
        ).scalars().all()
        return [alerta_academica_mapper.a_dominio(m) for m in modelos]

    def listar_pendientes(self, limite: int = 100) -> list[AlertaAcademica]:
        modelos = self._session.execute(
            select(AlertaAcademicaModel)
            .where(AlertaAcademicaModel.estado == EstadoAlertaAcademica.PENDIENTE)
            .limit(limite)
        ).scalars().all()
        return [alerta_academica_mapper.a_dominio(m) for m in modelos]
