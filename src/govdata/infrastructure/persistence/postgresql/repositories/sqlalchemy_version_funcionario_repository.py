"""Adaptador: SqlAlchemyVersionFuncionarioRepository."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.version_funcionario_repository_port import (
    VersionFuncionarioRepositoryPort,
)
from govdata.domain.entities.version_funcionario import EstadoVersion, VersionFuncionario
from govdata.infrastructure.persistence.postgresql.mappers import version_funcionario_mapper
from govdata.infrastructure.persistence.postgresql.models.version_funcionario_model import (
    VersionFuncionarioModel,
)


class SqlAlchemyVersionFuncionarioRepository(VersionFuncionarioRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, version: VersionFuncionario) -> VersionFuncionario:
        modelo_existente = self._session.get(VersionFuncionarioModel, version.id) if version.id else None
        modelo = version_funcionario_mapper.a_modelo(version, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return version_funcionario_mapper.a_dominio(modelo)

    def buscar_vigente(self, persona_id: int, entidad_id: int) -> VersionFuncionario | None:
        modelo = (
            self._session.execute(
                select(VersionFuncionarioModel).where(
                    VersionFuncionarioModel.persona_id == persona_id,
                    VersionFuncionarioModel.entidad_id == entidad_id,
                    VersionFuncionarioModel.estado == EstadoVersion.VIGENTE,
                )
            )
            .scalars()
            .first()
        )
        return version_funcionario_mapper.a_dominio(modelo) if modelo else None

    def listar_por_persona(self, persona_id: int) -> list[VersionFuncionario]:
        modelos = (
            self._session.execute(
                select(VersionFuncionarioModel)
                .where(VersionFuncionarioModel.persona_id == persona_id)
                .order_by(VersionFuncionarioModel.fecha_inicio.asc())
            )
            .scalars()
            .all()
        )
        return [version_funcionario_mapper.a_dominio(m) for m in modelos]

    def listar_por_entidad_y_cargo(self, entidad_id: int, cargo: str) -> list[VersionFuncionario]:
        modelos = (
            self._session.execute(
                select(VersionFuncionarioModel).where(
                    VersionFuncionarioModel.entidad_id == entidad_id, VersionFuncionarioModel.cargo == cargo
                )
            )
            .scalars()
            .all()
        )
        return [version_funcionario_mapper.a_dominio(m) for m in modelos]

    def buscar_vigente_por_entidad_y_cargo(self, entidad_id: int, cargo: str) -> VersionFuncionario | None:
        modelo = (
            self._session.execute(
                select(VersionFuncionarioModel).where(
                    VersionFuncionarioModel.entidad_id == entidad_id,
                    VersionFuncionarioModel.cargo == cargo,
                    VersionFuncionarioModel.estado == EstadoVersion.VIGENTE,
                )
            )
            .scalars()
            .first()
        )
        return version_funcionario_mapper.a_dominio(modelo) if modelo else None

    def buscar_vigente_en_fecha(self, entidad_id: int, cargo: str, en_fecha: date) -> VersionFuncionario | None:
        modelo = (
            self._session.execute(
                select(VersionFuncionarioModel).where(
                    VersionFuncionarioModel.entidad_id == entidad_id,
                    VersionFuncionarioModel.cargo == cargo,
                    VersionFuncionarioModel.fecha_inicio <= en_fecha,
                    (VersionFuncionarioModel.fecha_fin.is_(None)) | (VersionFuncionarioModel.fecha_fin >= en_fecha),
                )
            )
            .scalars()
            .first()
        )
        return version_funcionario_mapper.a_dominio(modelo) if modelo else None

    def listar_por_entidad(self, entidad_id: int) -> list[VersionFuncionario]:
        modelos = (
            self._session.execute(
                select(VersionFuncionarioModel).where(VersionFuncionarioModel.entidad_id == entidad_id)
            )
            .scalars()
            .all()
        )
        return [version_funcionario_mapper.a_dominio(m) for m in modelos]
