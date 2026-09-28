"""Puerto: HistorialCambiosRepositoryPort."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.historial_cambios import HistorialCambios


class HistorialCambiosRepositoryPort(ABC):
    """Persistencia de la trayectoria de cambios de cargo de cada persona."""

    @abstractmethod
    def registrar(self, cambio: HistorialCambios) -> HistorialCambios: ...

    @abstractmethod
    def listar_por_persona(self, persona_id: int) -> list[HistorialCambios]: ...
