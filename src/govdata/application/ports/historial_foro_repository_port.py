"""Puerto: HistorialForoRepositoryPort -- Submodulo 8.6."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.historial_foro import HistorialForo


class HistorialForoRepositoryPort(ABC):
    @abstractmethod
    def guardar_lote(self, registros: list[HistorialForo]) -> list[HistorialForo]: ...

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[HistorialForo]:
        """Bitacora completa de cambios de una PersonaMaster."""

    @abstractmethod
    def listar_todo(self) -> list[HistorialForo]:
        """Bitacora GLOBAL (todas las PersonaMaster) -- insumo de las
        Metricas agregadas (Submodulo 8.15)."""
