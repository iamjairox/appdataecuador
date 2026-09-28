"""Adaptador: SqlAlchemyAuditoriaComparacionRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.auditoria_comparacion_repository_port import (
    AuditoriaComparacionRepositoryPort,
)
from govdata.domain.entities.auditoria_comparacion import AuditoriaComparacion
from govdata.infrastructure.persistence.postgresql.mappers import auditoria_comparacion_mapper
from govdata.infrastructure.persistence.postgresql.models.auditoria_comparacion_model import (
    AuditoriaComparacionModel,
)


class SqlAlchemyAuditoriaComparacionRepository(AuditoriaComparacionRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def registrar(self, auditoria: AuditoriaComparacion) -> AuditoriaComparacion:
        modelo_existente = self._session.get(AuditoriaComparacionModel, auditoria.id) if auditoria.id else None
        modelo = auditoria_comparacion_mapper.a_modelo(auditoria, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return auditoria_comparacion_mapper.a_dominio(modelo)

    def listar_por_documento(self, documento_id: int) -> list[AuditoriaComparacion]:
        modelos = (
            self._session.execute(
                select(AuditoriaComparacionModel).where(AuditoriaComparacionModel.documento_id == documento_id)
            )
            .scalars()
            .all()
        )
        return [auditoria_comparacion_mapper.a_dominio(m) for m in modelos]
