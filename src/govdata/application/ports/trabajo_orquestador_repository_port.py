"""Puerto: TrabajoOrquestadorRepositoryPort -- Submodulos 9.6 (Cola de
Trabajos, persistida en PostgreSQL) / 9.7 (Reanudacion automatica) / 9.8
(Control de concurrencia: bloqueo optimista)."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from govdata.domain.entities.trabajo_orquestador import TrabajoOrquestador
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador


class TrabajoOrquestadorRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, trabajo: TrabajoOrquestador) -> TrabajoOrquestador:
        """Inserta o actualiza SIN verificar bloqueo optimista -- usado
        para altas nuevas o por el propio duenio de un `version_lock` ya
        confirmado. Ver `tomar_atomico` para la escritura QUE SI valida
        concurrencia."""

    @abstractmethod
    def buscar_por_id(self, trabajo_id: uuid.UUID) -> TrabajoOrquestador | None: ...

    @abstractmethod
    def listar_por_estado(self, estado: EstadoTrabajoOrquestador, limite: int = 500) -> list[TrabajoOrquestador]: ...

    @abstractmethod
    def listar_pendientes_ordenados_por_prioridad(self, limite: int = 500) -> list[TrabajoOrquestador]:
        """Candidatos EN_COLA o REINTENTANDO, ordenados por prioridad
        (Submodulo 9.5) -- insumo directo de la cola de ejecucion."""

    @abstractmethod
    def contar_por_estado(self) -> dict[EstadoTrabajoOrquestador, int]:
        """Insumo del Dashboard interno (Submodulo 9.11)."""

    @abstractmethod
    def tomar_atomico(self, trabajo_id: uuid.UUID, version_esperada: int) -> bool:
        """Intenta marcar el trabajo como tomado por ESTE worker mediante
        un UPDATE condicionado a `version_lock == version_esperada`
        (Submodulo 9.8, bloqueo optimista). Retorna `False` (nunca
        lanza) si otro worker ya lo tomo primero -- el llamador decide
        que hacer (tipicamente: pasar al siguiente candidato)."""
