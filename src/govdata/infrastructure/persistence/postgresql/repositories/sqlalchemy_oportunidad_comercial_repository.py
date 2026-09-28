"""Adaptador: SqlAlchemyOportunidadComercialRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.oportunidad_comercial_repository_port import (
    OportunidadComercialRepositoryPort,
)
from govdata.domain.entities.oportunidad_comercial import OportunidadComercial
from govdata.infrastructure.persistence.postgresql.mappers import oportunidad_comercial_mapper
from govdata.infrastructure.persistence.postgresql.models.oportunidad_comercial_model import (
    OportunidadComercialModel,
)


class SqlAlchemyOportunidadComercialRepository(OportunidadComercialRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, oportunidad: OportunidadComercial) -> OportunidadComercial:
        modelo_existente = self._session.get(OportunidadComercialModel, oportunidad.id)
        modelo = oportunidad_comercial_mapper.a_modelo(oportunidad, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return oportunidad_comercial_mapper.a_dominio(modelo)

    def guardar_lote(self, oportunidades: list[OportunidadComercial]) -> list[OportunidadComercial]:
        return [self.guardar(o) for o in oportunidades]

    def listar_por_entidad(self, entidad_id: int) -> list[OportunidadComercial]:
        modelos = (
            self._session.execute(
                select(OportunidadComercialModel).where(OportunidadComercialModel.entidad_id == entidad_id)
            )
            .scalars()
            .all()
        )
        return [oportunidad_comercial_mapper.a_dominio(m) for m in modelos]
