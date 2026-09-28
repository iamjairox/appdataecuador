"""Adaptador: SqlAlchemyDescargaRepository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from govdata.application.ports.descarga_repository_port import DescargaRepositoryPort
from govdata.domain.entities.descarga import Descarga
from govdata.infrastructure.persistence.postgresql.mappers import descarga_mapper
from govdata.infrastructure.persistence.postgresql.models.descarga_model import DescargaModel


class SqlAlchemyDescargaRepository(DescargaRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def registrar(self, descarga: Descarga) -> Descarga:
        modelo = descarga_mapper.a_modelo(descarga)
        self._session.add(modelo)
        self._session.flush()
        return descarga_mapper.a_dominio(modelo)

    def listar_por_documento(self, documento_id: int) -> list[Descarga]:
        modelos = (
            self._session.execute(
                select(DescargaModel)
                .where(DescargaModel.documento_id == documento_id)
                .order_by(DescargaModel.iniciado_en.desc())
            )
            .scalars()
            .all()
        )
        return [descarga_mapper.a_dominio(m) for m in modelos]

    def contar_intentos(self, documento_id: int) -> int:
        return (
            self._session.execute(
                select(func.count(DescargaModel.id)).where(DescargaModel.documento_id == documento_id)
            ).scalar_one()
            or 0
        )
