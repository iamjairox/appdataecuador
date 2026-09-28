"""Puerto: EventoRepositoryPort -- Submodulo 5.7 (Notificaciones, preparacion)."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from govdata.domain.entities.evento import Evento


class EventoRepositoryPort(ABC):
    """Persistencia de la cola de eventos (PENDIENTE -> CONSUMIDO -> PROCESADO)."""

    @abstractmethod
    def guardar(self, evento: Evento) -> Evento: ...

    @abstractmethod
    def guardar_lote(self, eventos: list[Evento]) -> list[Evento]: ...

    @abstractmethod
    def buscar_por_id(self, evento_id: uuid.UUID) -> Evento | None: ...

    @abstractmethod
    def listar_pendientes(self, limite: int) -> list[Evento]:
        """Eventos en estado PENDIENTE, mas antiguos primero -- lo que un
        futuro consumidor (n8n/Dashboard/API) leeria."""
