"""Adaptador: SqlAlchemyPublicacionRepository."""

from __future__ import annotations

from datetime import date

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from govdata.application.ports.publicacion_repository_port import PublicacionRepositoryPort
from govdata.domain.entities.publicacion import PublicacionMensual
from govdata.infrastructure.persistence.postgresql.mappers import publicacion_mapper
from govdata.infrastructure.persistence.postgresql.models.publicacion_model import PublicacionModel


class SqlAlchemyPublicacionRepository(PublicacionRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar_o_actualizar(self, publicacion: PublicacionMensual) -> PublicacionMensual:
        modelo_existente = (
            self._session.execute(
                select(PublicacionModel).where(
                    PublicacionModel.entidad_id == publicacion.entidad_id,
                    PublicacionModel.mes_publicado == publicacion.mes_publicado,
                )
            )
            .scalars()
            .first()
        )
        modelo = publicacion_mapper.a_modelo(publicacion, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return publicacion_mapper.a_dominio(modelo)

    def buscar_por_entidad_y_mes(
        self, entidad_id: int, mes_publicado: date
    ) -> PublicacionMensual | None:
        modelo = (
            self._session.execute(
                select(PublicacionModel).where(
                    PublicacionModel.entidad_id == entidad_id,
                    PublicacionModel.mes_publicado == mes_publicado,
                )
            )
            .scalars()
            .first()
        )
        return publicacion_mapper.a_dominio(modelo) if modelo else None

    def buscar_ultima_por_entidad(
        self, entidad_id: int, excluir_mes: date | None = None
    ) -> PublicacionMensual | None:
        condiciones = [PublicacionModel.entidad_id == entidad_id]
        if excluir_mes is not None:
            condiciones.append(PublicacionModel.mes_publicado != excluir_mes)
        modelo = (
            self._session.execute(
                select(PublicacionModel).where(*condiciones).order_by(desc(PublicacionModel.mes_publicado))
            )
            .scalars()
            .first()
        )
        return publicacion_mapper.a_dominio(modelo) if modelo else None
