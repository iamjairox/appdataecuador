"""Adaptador: SqlAlchemyPersonaMasterRepository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.value_objects.estado_persona_master import EstadoPersonaMaster
from govdata.infrastructure.persistence.postgresql.mappers import persona_master_mapper
from govdata.infrastructure.persistence.postgresql.models.persona_master_model import (
    PersonaMasterModel,
)


class SqlAlchemyPersonaMasterRepository(PersonaMasterRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, persona_master: PersonaMaster) -> PersonaMaster:
        modelo_existente = self._session.get(PersonaMasterModel, persona_master.id) if persona_master.id else None
        modelo = persona_master_mapper.a_modelo(persona_master, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return persona_master_mapper.a_dominio(modelo)

    def buscar_por_id(self, persona_master_id: int) -> PersonaMaster | None:
        modelo = self._session.get(PersonaMasterModel, persona_master_id)
        return persona_master_mapper.a_dominio(modelo) if modelo else None

    def buscar_por_persona_id(self, persona_id: int) -> PersonaMaster | None:
        modelo = self._session.execute(
            select(PersonaMasterModel).where(PersonaMasterModel.persona_id == persona_id)
        ).scalar_one_or_none()
        return persona_master_mapper.a_dominio(modelo) if modelo else None

    def buscar_por_fingerprint_principal(self, fingerprint: str) -> PersonaMaster | None:
        modelo = self._session.execute(
            select(PersonaMasterModel).where(
                PersonaMasterModel.fingerprint_principal == fingerprint,
                PersonaMasterModel.estado != EstadoPersonaMaster.FUSIONADA,
            )
        ).scalars().first()
        return persona_master_mapper.a_dominio(modelo) if modelo else None

    def buscar_candidatas_por_fingerprint_fonetico(self, fingerprint_fonetico: str) -> list[PersonaMaster]:
        modelos = self._session.execute(
            select(PersonaMasterModel).where(
                PersonaMasterModel.fingerprint_fonetico == fingerprint_fonetico,
                PersonaMasterModel.estado != EstadoPersonaMaster.FUSIONADA,
            )
        ).scalars().all()
        return [persona_master_mapper.a_dominio(m) for m in modelos]

    def buscar_candidatas_por_correo(self, correo: str) -> list[PersonaMaster]:
        modelos = self._session.execute(
            select(PersonaMasterModel).where(
                PersonaMasterModel.correo_principal == correo.strip().lower(),
                PersonaMasterModel.estado != EstadoPersonaMaster.FUSIONADA,
            )
        ).scalars().all()
        return [persona_master_mapper.a_dominio(m) for m in modelos]

    def listar_activas(self, limite: int, offset: int = 0) -> list[PersonaMaster]:
        modelos = self._session.execute(
            select(PersonaMasterModel)
            .where(PersonaMasterModel.estado != EstadoPersonaMaster.FUSIONADA)
            .order_by(PersonaMasterModel.id)
            .limit(limite)
            .offset(offset)
        ).scalars().all()
        return [persona_master_mapper.a_dominio(m) for m in modelos]

    def contar_activas(self) -> int:
        total = self._session.execute(
            select(func.count()).select_from(PersonaMasterModel).where(
                PersonaMasterModel.estado != EstadoPersonaMaster.FUSIONADA
            )
        ).scalar_one()
        return int(total)
