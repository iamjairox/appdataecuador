"""Puerto: AlertaForoRepositoryPort -- Submodulo 8.7."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from govdata.domain.entities.alerta_foro import AlertaForo


class AlertaForoRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, alerta: AlertaForo) -> AlertaForo: ...

    @abstractmethod
    def guardar_lote(self, alertas: list[AlertaForo]) -> list[AlertaForo]: ...

    @abstractmethod
    def buscar_por_id(self, alerta_id: uuid.UUID) -> AlertaForo | None: ...

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaForo]: ...

    @abstractmethod
    def listar_pendientes(self, limite: int = 100) -> list[AlertaForo]:
        """Insumo del Programador de Enriquecimiento y de priorizacion
        (mismo patron que `AlertaAcademicaRepositoryPort`, Modulo 7)."""
