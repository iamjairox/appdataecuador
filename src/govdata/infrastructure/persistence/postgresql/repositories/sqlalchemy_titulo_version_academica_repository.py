"""Adaptador: SqlAlchemyTituloVersionAcademicaRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.titulo_version_repository_port import TituloVersionRepositoryPort
from govdata.domain.entities.titulo_version_academica import (
    EstadoVersionAcademica,
    TituloVersionAcademica,
)
from govdata.infrastructure.persistence.postgresql.mappers import titulo_version_academica_mapper
from govdata.infrastructure.persistence.postgresql.models.titulo_version_academica_model import (
    TituloVersionAcademicaModel,
)


class SqlAlchemyTituloVersionAcademicaRepository(TituloVersionRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, version: TituloVersionAcademica) -> TituloVersionAcademica:
        modelo_existente = self._session.get(TituloVersionAcademicaModel, version.id) if version.id else None
        modelo = titulo_version_academica_mapper.a_modelo(version, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return titulo_version_academica_mapper.a_dominio(modelo)

    def buscar_vigente(self, persona_master_id: int, clave_titulo: str) -> TituloVersionAcademica | None:
        modelo = self._session.execute(
            select(TituloVersionAcademicaModel).where(
                TituloVersionAcademicaModel.persona_master_id == persona_master_id,
                TituloVersionAcademicaModel.clave_titulo == clave_titulo,
                TituloVersionAcademicaModel.estado_version == EstadoVersionAcademica.VIGENTE,
            )
        ).scalar_one_or_none()
        return titulo_version_academica_mapper.a_dominio(modelo) if modelo else None

    def listar_historial(self, persona_master_id: int, clave_titulo: str) -> list[TituloVersionAcademica]:
        modelos = self._session.execute(
            select(TituloVersionAcademicaModel)
            .where(
                TituloVersionAcademicaModel.persona_master_id == persona_master_id,
                TituloVersionAcademicaModel.clave_titulo == clave_titulo,
            )
            .order_by(TituloVersionAcademicaModel.numero_version)
        ).scalars().all()
        return [titulo_version_academica_mapper.a_dominio(m) for m in modelos]

    def listar_por_persona_master(self, persona_master_id: int) -> list[TituloVersionAcademica]:
        modelos = self._session.execute(
            select(TituloVersionAcademicaModel).where(
                TituloVersionAcademicaModel.persona_master_id == persona_master_id
            )
        ).scalars().all()
        return [titulo_version_academica_mapper.a_dominio(m) for m in modelos]
