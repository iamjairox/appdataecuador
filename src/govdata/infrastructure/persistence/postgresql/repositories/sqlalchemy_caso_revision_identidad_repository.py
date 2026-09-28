"""Adaptador: SqlAlchemyCasoRevisionIdentidadRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.caso_revision_identidad_repository_port import (
    CasoRevisionIdentidadRepositoryPort,
)
from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad
from govdata.domain.value_objects.estado_revision_identidad import EstadoRevisionIdentidad
from govdata.infrastructure.persistence.postgresql.mappers import caso_revision_identidad_mapper
from govdata.infrastructure.persistence.postgresql.models.caso_revision_identidad_model import (
    CasoRevisionIdentidadModel,
)


class SqlAlchemyCasoRevisionIdentidadRepository(CasoRevisionIdentidadRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, caso: CasoRevisionIdentidad) -> CasoRevisionIdentidad:
        modelo_existente = self._session.get(CasoRevisionIdentidadModel, caso.uuid)
        modelo = caso_revision_identidad_mapper.a_modelo(caso, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return caso_revision_identidad_mapper.a_dominio(modelo)

    def buscar_por_id(self, caso_id: uuid.UUID) -> CasoRevisionIdentidad | None:
        modelo = self._session.get(CasoRevisionIdentidadModel, caso_id)
        return caso_revision_identidad_mapper.a_dominio(modelo) if modelo else None

    def listar_pendientes(self, limite: int = 100) -> list[CasoRevisionIdentidad]:
        modelos = self._session.execute(
            select(CasoRevisionIdentidadModel)
            .where(CasoRevisionIdentidadModel.estado == EstadoRevisionIdentidad.PENDIENTE_REVISION)
            .order_by(CasoRevisionIdentidadModel.creado_en)
            .limit(limite)
        ).scalars().all()
        return [caso_revision_identidad_mapper.a_dominio(m) for m in modelos]

    def buscar_pendiente_entre(
        self, persona_master_id_a: int, persona_master_id_b: int
    ) -> CasoRevisionIdentidad | None:
        modelo = self._session.execute(
            select(CasoRevisionIdentidadModel).where(
                CasoRevisionIdentidadModel.estado == EstadoRevisionIdentidad.PENDIENTE_REVISION,
                (
                    (
                        (CasoRevisionIdentidadModel.persona_master_id_a == persona_master_id_a)
                        & (CasoRevisionIdentidadModel.persona_master_id_b == persona_master_id_b)
                    )
                    | (
                        (CasoRevisionIdentidadModel.persona_master_id_a == persona_master_id_b)
                        & (CasoRevisionIdentidadModel.persona_master_id_b == persona_master_id_a)
                    )
                ),
            )
        ).scalars().first()
        return caso_revision_identidad_mapper.a_dominio(modelo) if modelo else None
