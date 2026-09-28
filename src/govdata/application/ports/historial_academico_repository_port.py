"""Puerto: HistorialAcademicoRepositoryPort -- Submodulo 7.14."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.historial_academico import HistorialAcademico


class HistorialAcademicoRepositoryPort(ABC):
    @abstractmethod
    def guardar_lote(self, registros: list[HistorialAcademico]) -> list[HistorialAcademico]: ...

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[HistorialAcademico]:
        """Bitacora completa de cambios -- insumo directo del contrato
        oficial (`historial`, Submodulo 7.16)."""

    @abstractmethod
    def listar_todo(self) -> list[HistorialAcademico]:
        """Bitacora GLOBAL (todas las PersonaMaster) -- insumo de las
        Metricas agregadas (Submodulo 7.18: "cambios detectados",
        "titulos nuevos")."""
