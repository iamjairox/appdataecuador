"""Adaptador: SqlAlchemyVerificacionRepository."""

from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from govdata.application.ports.verificacion_repository_port import VerificacionRepositoryPort
from govdata.domain.entities.verificacion import Verificacion
from govdata.infrastructure.persistence.postgresql.mappers import verificacion_mapper
from govdata.infrastructure.persistence.postgresql.models.verificacion_model import (
    VerificacionModel,
)


class SqlAlchemyVerificacionRepository(VerificacionRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def registrar(self, verificacion: Verificacion) -> Verificacion:
        modelo = verificacion_mapper.a_modelo(verificacion)
        self._session.add(modelo)
        self._session.flush()
        return verificacion_mapper.a_dominio(modelo)

    def listar_por_entidad(self, entidad_id: int) -> list[Verificacion]:
        modelos = (
            self._session.execute(
                select(VerificacionModel)
                .where(VerificacionModel.entidad_id == entidad_id)
                .order_by(VerificacionModel.verificado_en.asc())
            )
            .scalars()
            .all()
        )
        return [verificacion_mapper.a_dominio(m) for m in modelos]

    def buscar_ultima_por_entidad(self, entidad_id: int) -> Verificacion | None:
        modelo = (
            self._session.execute(
                select(VerificacionModel)
                .where(VerificacionModel.entidad_id == entidad_id)
                .order_by(desc(VerificacionModel.verificado_en))
            )
            .scalars()
            .first()
        )
        return verificacion_mapper.a_dominio(modelo) if modelo else None
