"""Adaptador: SqlAlchemyRegistroForoRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.registro_foro_repository_port import RegistroForoRepositoryPort
from govdata.domain.entities.registro_foro import RegistroForo
from govdata.infrastructure.persistence.postgresql.mappers import registro_foro_mapper
from govdata.infrastructure.persistence.postgresql.models.registro_foro_model import (
    RegistroForoModel,
)


class SqlAlchemyRegistroForoRepository(RegistroForoRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, registro: RegistroForo) -> RegistroForo:
        modelo_existente = self._session.get(RegistroForoModel, registro.id) if registro.id else None
        modelo = registro_foro_mapper.a_modelo(registro, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return registro_foro_mapper.a_dominio(modelo)

    def buscar_vigente_por_clave(self, persona_master_id: int, clave_registro: str) -> RegistroForo | None:
        modelo = self._session.execute(
            select(RegistroForoModel).where(
                RegistroForoModel.persona_master_id == persona_master_id,
                RegistroForoModel.clave_registro == clave_registro,
                RegistroForoModel.vigente.is_(True),
            )
        ).scalar_one_or_none()
        return registro_foro_mapper.a_dominio(modelo) if modelo else None

    def listar_vigentes_por_persona_master(self, persona_master_id: int) -> list[RegistroForo]:
        modelos = self._session.execute(
            select(RegistroForoModel).where(
                RegistroForoModel.persona_master_id == persona_master_id,
                RegistroForoModel.vigente.is_(True),
            )
        ).scalars().all()
        return [registro_foro_mapper.a_dominio(m) for m in modelos]
