"""Adaptador: SqlAlchemyRegistroForoVersionRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.registro_foro_version_repository_port import (
    RegistroForoVersionRepositoryPort,
)
from govdata.domain.entities.registro_foro_version import EstadoVersionForo, RegistroForoVersion
from govdata.infrastructure.persistence.postgresql.mappers import registro_foro_version_mapper
from govdata.infrastructure.persistence.postgresql.models.registro_foro_version_model import (
    RegistroForoVersionModel,
)


class SqlAlchemyRegistroForoVersionRepository(RegistroForoVersionRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, version: RegistroForoVersion) -> RegistroForoVersion:
        modelo_existente = self._session.get(RegistroForoVersionModel, version.id) if version.id else None
        modelo = registro_foro_version_mapper.a_modelo(version, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return registro_foro_version_mapper.a_dominio(modelo)

    def buscar_vigente(self, persona_master_id: int, clave_registro: str) -> RegistroForoVersion | None:
        modelo = self._session.execute(
            select(RegistroForoVersionModel).where(
                RegistroForoVersionModel.persona_master_id == persona_master_id,
                RegistroForoVersionModel.clave_registro == clave_registro,
                RegistroForoVersionModel.estado_version == EstadoVersionForo.VIGENTE,
            )
        ).scalar_one_or_none()
        return registro_foro_version_mapper.a_dominio(modelo) if modelo else None

    def listar_historial(self, persona_master_id: int, clave_registro: str) -> list[RegistroForoVersion]:
        modelos = self._session.execute(
            select(RegistroForoVersionModel)
            .where(
                RegistroForoVersionModel.persona_master_id == persona_master_id,
                RegistroForoVersionModel.clave_registro == clave_registro,
            )
            .order_by(RegistroForoVersionModel.numero_version)
        ).scalars().all()
        return [registro_foro_version_mapper.a_dominio(m) for m in modelos]

    def listar_por_persona_master(self, persona_master_id: int) -> list[RegistroForoVersion]:
        modelos = self._session.execute(
            select(RegistroForoVersionModel).where(RegistroForoVersionModel.persona_master_id == persona_master_id)
        ).scalars().all()
        return [registro_foro_version_mapper.a_dominio(m) for m in modelos]
