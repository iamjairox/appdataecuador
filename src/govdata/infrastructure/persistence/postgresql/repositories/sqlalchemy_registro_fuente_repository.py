"""Adaptador: SqlAlchemyRegistroFuenteRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.registro_fuente_repository_port import RegistroFuenteRepositoryPort
from govdata.domain.entities.registro_fuente import RegistroFuente
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.infrastructure.persistence.postgresql.mappers import registro_fuente_mapper
from govdata.infrastructure.persistence.postgresql.models.registro_fuente_model import (
    RegistroFuenteModel,
)


class SqlAlchemyRegistroFuenteRepository(RegistroFuenteRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, registro: RegistroFuente) -> RegistroFuente:
        modelo_existente = self._session.get(RegistroFuenteModel, registro.id) if registro.id else None
        modelo = registro_fuente_mapper.a_modelo(registro, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return registro_fuente_mapper.a_dominio(modelo)

    def buscar_vigente(self, persona_master_id: int, fuente: FuenteExterna) -> RegistroFuente | None:
        modelo = self._session.execute(
            select(RegistroFuenteModel).where(
                RegistroFuenteModel.persona_master_id == persona_master_id,
                RegistroFuenteModel.fuente == fuente,
                RegistroFuenteModel.vigente.is_(True),
            )
        ).scalar_one_or_none()
        return registro_fuente_mapper.a_dominio(modelo) if modelo else None

    def listar_por_persona_master(self, persona_master_id: int) -> list[RegistroFuente]:
        modelos = self._session.execute(
            select(RegistroFuenteModel).where(RegistroFuenteModel.persona_master_id == persona_master_id)
        ).scalars().all()
        return [registro_fuente_mapper.a_dominio(m) for m in modelos]

    def listar_historial(self, persona_master_id: int, fuente: FuenteExterna) -> list[RegistroFuente]:
        modelos = self._session.execute(
            select(RegistroFuenteModel)
            .where(RegistroFuenteModel.persona_master_id == persona_master_id, RegistroFuenteModel.fuente == fuente)
            .order_by(RegistroFuenteModel.version)
        ).scalars().all()
        return [registro_fuente_mapper.a_dominio(m) for m in modelos]
