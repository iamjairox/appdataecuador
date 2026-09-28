"""Puerto: EventoPerfilRepositoryPort -- Submodulo 6.12."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from govdata.domain.entities.evento_perfil import EventoPerfil


class EventoPerfilRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, evento: EventoPerfil) -> EventoPerfil: ...

    @abstractmethod
    def guardar_lote(self, eventos: list[EventoPerfil]) -> list[EventoPerfil]: ...

    @abstractmethod
    def buscar_por_id(self, evento_id: uuid.UUID) -> EventoPerfil | None: ...

    @abstractmethod
    def listar_pendientes(self, limite: int = 100) -> list[EventoPerfil]: ...

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[EventoPerfil]: ...
