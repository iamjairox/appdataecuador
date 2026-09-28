"""Puerto: EventoForoRepositoryPort -- Submodulo 8.7."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from govdata.domain.entities.evento_foro import EventoForo


class EventoForoRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, evento: EventoForo) -> EventoForo: ...

    @abstractmethod
    def guardar_lote(self, eventos: list[EventoForo]) -> list[EventoForo]: ...

    @abstractmethod
    def buscar_por_id(self, evento_id: uuid.UUID) -> EventoForo | None: ...

    @abstractmethod
    def listar_pendientes(self, limite: int = 100) -> list[EventoForo]: ...

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[EventoForo]: ...
