"""Puerto: EventoAcademicoRepositoryPort -- Submodulo 7.9."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from govdata.domain.entities.evento_academico import EventoAcademico


class EventoAcademicoRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, evento: EventoAcademico) -> EventoAcademico: ...

    @abstractmethod
    def guardar_lote(self, eventos: list[EventoAcademico]) -> list[EventoAcademico]: ...

    @abstractmethod
    def buscar_por_id(self, evento_id: uuid.UUID) -> EventoAcademico | None: ...

    @abstractmethod
    def listar_pendientes(self, limite: int = 100) -> list[EventoAcademico]: ...

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[EventoAcademico]: ...
