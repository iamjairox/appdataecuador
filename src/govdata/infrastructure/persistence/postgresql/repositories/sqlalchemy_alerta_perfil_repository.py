"""Adaptador: SqlAlchemyAlertaPerfilRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.alerta_perfil_repository_port import AlertaPerfilRepositoryPort
from govdata.domain.entities.alerta_perfil import AlertaPerfil
from govdata.infrastructure.persistence.postgresql.mappers import alerta_perfil_mapper
from govdata.infrastructure.persistence.postgresql.models.alerta_perfil_model import (
    AlertaPerfilModel,
)


class SqlAlchemyAlertaPerfilRepository(AlertaPerfilRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, alerta: AlertaPerfil) -> AlertaPerfil:
        modelo_existente = self._session.get(AlertaPerfilModel, alerta.id)
        modelo = alerta_perfil_mapper.a_modelo(alerta, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return alerta_perfil_mapper.a_dominio(modelo)

    def guardar_lote(self, alertas: list[AlertaPerfil]) -> list[AlertaPerfil]:
        return [self.guardar(a) for a in alertas]

    def buscar_por_id(self, alerta_id: uuid.UUID) -> AlertaPerfil | None:
        modelo = self._session.get(AlertaPerfilModel, alerta_id)
        return alerta_perfil_mapper.a_dominio(modelo) if modelo else None

    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaPerfil]:
        modelos = self._session.execute(
            select(AlertaPerfilModel).where(AlertaPerfilModel.persona_master_id == persona_master_id)
        ).scalars().all()
        return [alerta_perfil_mapper.a_dominio(m) for m in modelos]
