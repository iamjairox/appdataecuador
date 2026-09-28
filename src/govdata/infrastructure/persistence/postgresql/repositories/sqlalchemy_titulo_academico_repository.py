"""Adaptador: SqlAlchemyTituloAcademicoRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.titulo_academico_repository_port import (
    TituloAcademicoRepositoryPort,
)
from govdata.domain.entities.titulo_academico import TituloAcademico
from govdata.infrastructure.persistence.postgresql.mappers import titulo_academico_mapper
from govdata.infrastructure.persistence.postgresql.models.titulo_academico_model import (
    TituloAcademicoModel,
)


class SqlAlchemyTituloAcademicoRepository(TituloAcademicoRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, titulo: TituloAcademico) -> TituloAcademico:
        modelo_existente = self._session.get(TituloAcademicoModel, titulo.id) if titulo.id else None
        modelo = titulo_academico_mapper.a_modelo(titulo, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return titulo_academico_mapper.a_dominio(modelo)

    def buscar_vigente_por_clave(self, persona_master_id: int, clave_titulo: str) -> TituloAcademico | None:
        modelo = self._session.execute(
            select(TituloAcademicoModel).where(
                TituloAcademicoModel.persona_master_id == persona_master_id,
                TituloAcademicoModel.clave_titulo == clave_titulo,
                TituloAcademicoModel.vigente.is_(True),
            )
        ).scalar_one_or_none()
        return titulo_academico_mapper.a_dominio(modelo) if modelo else None

    def listar_vigentes_por_persona_master(self, persona_master_id: int) -> list[TituloAcademico]:
        modelos = self._session.execute(
            select(TituloAcademicoModel).where(
                TituloAcademicoModel.persona_master_id == persona_master_id,
                TituloAcademicoModel.vigente.is_(True),
            )
        ).scalars().all()
        return [titulo_academico_mapper.a_dominio(m) for m in modelos]
