"""Adaptador: SqlAlchemyEjecucionRepository."""

from __future__ import annotations

from sqlalchemy.orm import Session

from govdata.application.ports.ejecucion_repository_port import EjecucionRepositoryPort
from govdata.domain.entities.ejecucion import Ejecucion
from govdata.infrastructure.persistence.postgresql.mappers import ejecucion_mapper
from govdata.infrastructure.persistence.postgresql.models.ejecucion_model import EjecucionModel


class SqlAlchemyEjecucionRepository(EjecucionRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def registrar(self, ejecucion: Ejecucion) -> Ejecucion:
        modelo = ejecucion_mapper.a_modelo(ejecucion)
        self._session.add(modelo)
        self._session.flush()
        return ejecucion_mapper.a_dominio(modelo)

    def actualizar(self, ejecucion: Ejecucion) -> Ejecucion:
        modelo = self._session.get(EjecucionModel, ejecucion.id)
        if modelo is None:
            return self.registrar(ejecucion)
        ejecucion_mapper.a_modelo(ejecucion, modelo)
        self._session.flush()
        return ejecucion_mapper.a_dominio(modelo)
