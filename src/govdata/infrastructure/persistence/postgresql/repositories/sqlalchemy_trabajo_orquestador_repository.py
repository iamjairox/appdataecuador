"""Adaptador: SqlAlchemyTrabajoOrquestadorRepository -- Submodulos
9.6/9.7/9.8.

`tomar_atomico` es la UNICA operacion de escritura de este repositorio
que NO pasa por `guardar()`: hace un `UPDATE ... WHERE id = ? AND
version_lock = ?` directo (Submodulo 9.8, bloqueo optimista) -- si el
`rowcount` resultante es 0, otro worker ya gano la carrera, y se retorna
`False` sin lanzar nada (el llamador decide que hacer, tipicamente pasar
al siguiente candidato de la cola)."""

from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import CursorResult, case, func, select, update
from sqlalchemy.orm import Session

from govdata.application.ports.trabajo_orquestador_repository_port import (
    TrabajoOrquestadorRepositoryPort,
)
from govdata.domain.entities.trabajo_orquestador import TrabajoOrquestador
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion
from govdata.infrastructure.persistence.postgresql.mappers import trabajo_orquestador_mapper
from govdata.infrastructure.persistence.postgresql.models.trabajo_orquestador_model import (
    TrabajoOrquestadorModel,
)

_ORDEN_PRIORIDAD = {
    NivelPrioridadEjecucion.MUY_ALTA: 3, NivelPrioridadEjecucion.ALTA: 2,
    NivelPrioridadEjecucion.MEDIA: 1, NivelPrioridadEjecucion.BAJA: 0,
}


class SqlAlchemyTrabajoOrquestadorRepository(TrabajoOrquestadorRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, trabajo: TrabajoOrquestador) -> TrabajoOrquestador:
        modelo_existente = self._session.get(TrabajoOrquestadorModel, trabajo.id)
        modelo = trabajo_orquestador_mapper.a_modelo(trabajo, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return trabajo_orquestador_mapper.a_dominio(modelo)

    def buscar_por_id(self, trabajo_id: uuid.UUID) -> TrabajoOrquestador | None:
        modelo = self._session.get(TrabajoOrquestadorModel, trabajo_id)
        return trabajo_orquestador_mapper.a_dominio(modelo) if modelo else None

    def listar_por_estado(self, estado: EstadoTrabajoOrquestador, limite: int = 500) -> list[TrabajoOrquestador]:
        modelos = self._session.execute(
            select(TrabajoOrquestadorModel).where(TrabajoOrquestadorModel.estado == estado).limit(limite)
        ).scalars().all()
        return [trabajo_orquestador_mapper.a_dominio(m) for m in modelos]

    def listar_pendientes_ordenados_por_prioridad(self, limite: int = 500) -> list[TrabajoOrquestador]:
        orden_prioridad = case(
            *((TrabajoOrquestadorModel.prioridad == valor, peso) for valor, peso in _ORDEN_PRIORIDAD.items()),
            else_=0,
        )
        candidatos = (EstadoTrabajoOrquestador.EN_COLA, EstadoTrabajoOrquestador.REINTENTANDO)
        modelos = self._session.execute(
            select(TrabajoOrquestadorModel)
            .where(TrabajoOrquestadorModel.estado.in_(candidatos))
            .order_by(orden_prioridad.desc(), TrabajoOrquestadorModel.creado_en.asc())
            .limit(limite)
        ).scalars().all()
        return [trabajo_orquestador_mapper.a_dominio(m) for m in modelos]

    def contar_por_estado(self) -> dict[EstadoTrabajoOrquestador, int]:
        filas = self._session.execute(
            select(TrabajoOrquestadorModel.estado, func.count()).group_by(TrabajoOrquestadorModel.estado)
        ).all()
        return {estado: cantidad for estado, cantidad in filas}

    def tomar_atomico(self, trabajo_id: uuid.UUID, version_esperada: int) -> bool:
        resultado = cast(
            CursorResult,
            self._session.execute(
                update(TrabajoOrquestadorModel)
                .where(
                    TrabajoOrquestadorModel.id == trabajo_id,
                    TrabajoOrquestadorModel.version_lock == version_esperada,
                )
                .values(estado=EstadoTrabajoOrquestador.EJECUTANDO, version_lock=version_esperada + 1)
            ),
        )
        self._session.flush()
        return resultado.rowcount == 1
