"""Adaptador: SqlAlchemyAtributoTrazableRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.atributo_trazable_repository_port import (
    AtributoTrazableRepositoryPort,
)
from govdata.domain.entities.atributo_trazable import AtributoTrazable
from govdata.infrastructure.persistence.postgresql.mappers import atributo_trazable_mapper
from govdata.infrastructure.persistence.postgresql.models.atributo_trazable_model import (
    AtributoTrazableModel,
)


class SqlAlchemyAtributoTrazableRepository(AtributoTrazableRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar_lote(self, atributos: list[AtributoTrazable]) -> list[AtributoTrazable]:
        guardados = []
        for atributo in atributos:
            modelo = atributo_trazable_mapper.a_modelo(atributo)
            self._session.add(modelo)
            guardados.append(modelo)
        self._session.flush()
        return [atributo_trazable_mapper.a_dominio(m) for m in guardados]

    def listar_por_persona_master(self, persona_master_id: int) -> list[AtributoTrazable]:
        modelos = self._session.execute(
            select(AtributoTrazableModel).where(AtributoTrazableModel.persona_master_id == persona_master_id)
        ).scalars().all()
        return [atributo_trazable_mapper.a_dominio(m) for m in modelos]
