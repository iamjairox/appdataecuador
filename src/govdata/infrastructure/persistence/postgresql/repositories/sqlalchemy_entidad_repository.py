"""Adaptador: SqlAlchemyEntidadRepository.

Implementacion concreta de `EntidadRepositoryPort` sobre PostgreSQL (via
SQLAlchemy). El resto del sistema depende del puerto, nunca de esta clase
directamente -- se inyecta por el DI Container.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from govdata.application.ports.entidad_repository_port import EntidadRepositoryPort
from govdata.domain.entities.entidad import Entidad
from govdata.infrastructure.persistence.postgresql.mappers import entidad_mapper
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel


class SqlAlchemyEntidadRepository(EntidadRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar_o_actualizar(self, entidad: Entidad) -> Entidad:
        modelo_existente = (
            self._session.execute(
                select(EntidadModel).where(EntidadModel.url_transparencia == entidad.url_transparencia)
            )
            .scalars()
            .first()
        )
        modelo = entidad_mapper.a_modelo(entidad, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return entidad_mapper.a_dominio(modelo)

    def buscar_por_id(self, entidad_id: int) -> Entidad | None:
        modelo = self._session.get(EntidadModel, entidad_id)
        return entidad_mapper.a_dominio(modelo) if modelo else None

    def buscar_por_url(self, url_transparencia: str) -> Entidad | None:
        modelo = (
            self._session.execute(
                select(EntidadModel).where(EntidadModel.url_transparencia == url_transparencia)
            )
            .scalars()
            .first()
        )
        return entidad_mapper.a_dominio(modelo) if modelo else None

    def listar_activas(self, portal_origen: str | None = None) -> list[Entidad]:
        consulta = select(EntidadModel).where(EntidadModel.activo.is_(True))
        if portal_origen:
            consulta = consulta.where(EntidadModel.portal_origen == portal_origen)
        modelos = self._session.execute(consulta).scalars().all()
        return [entidad_mapper.a_dominio(m) for m in modelos]

    def buscar_por_nombre(self, fragmento_nombre: str) -> Entidad | None:
        modelo = (
            self._session.execute(
                select(EntidadModel)
                .where(func.lower(EntidadModel.nombre).contains(fragmento_nombre.lower()))
                .order_by(func.length(EntidadModel.nombre).asc())
            )
            .scalars()
            .first()
        )
        return entidad_mapper.a_dominio(modelo) if modelo else None
