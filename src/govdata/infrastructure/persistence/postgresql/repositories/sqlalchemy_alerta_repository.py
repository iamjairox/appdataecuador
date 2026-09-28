"""Adaptador: SqlAlchemyAlertaRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.alerta_repository_port import AlertaRepositoryPort
from govdata.domain.entities.alerta import Alerta
from govdata.infrastructure.persistence.postgresql.mappers import alerta_mapper
from govdata.infrastructure.persistence.postgresql.models.alerta_model import AlertaModel


class SqlAlchemyAlertaRepository(AlertaRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, alerta: Alerta) -> Alerta:
        modelo_existente = self._session.get(AlertaModel, alerta.id)
        modelo = alerta_mapper.a_modelo(alerta, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return alerta_mapper.a_dominio(modelo)

    def guardar_lote(self, alertas: list[Alerta]) -> list[Alerta]:
        return [self.guardar(a) for a in alertas]

    def buscar_por_id(self, alerta_id: uuid.UUID) -> Alerta | None:
        modelo = self._session.get(AlertaModel, alerta_id)
        return alerta_mapper.a_dominio(modelo) if modelo else None

    def listar_por_entidad(self, entidad_id: int) -> list[Alerta]:
        modelos = self._session.execute(select(AlertaModel).where(AlertaModel.entidad_id == entidad_id)).scalars().all()
        return [alerta_mapper.a_dominio(m) for m in modelos]

    def listar_por_documento(self, documento_id: int) -> list[Alerta]:
        modelos = (
            self._session.execute(select(AlertaModel).where(AlertaModel.documento_id == documento_id)).scalars().all()
        )
        return [alerta_mapper.a_dominio(m) for m in modelos]
