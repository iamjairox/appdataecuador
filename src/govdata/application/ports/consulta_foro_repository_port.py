"""Puerto: ConsultaForoRepositoryPort -- Submodulo 8.17."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from govdata.domain.entities.consulta_foro import ConsultaForo


class ConsultaForoRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, consulta: ConsultaForo) -> ConsultaForo: ...

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[ConsultaForo]: ...

    @abstractmethod
    def ultima_consulta(self, persona_master_id: int) -> ConsultaForo | None:
        """El intento mas reciente (exitoso o no) -- insumo del Cache por
        Persona (Submodulo 8.8)."""

    @abstractmethod
    def listar_todas(self, desde: datetime | None = None) -> list[ConsultaForo]:
        """Todas las consultas (opcionalmente desde una fecha) -- insumo
        de las Metricas (Submodulo 8.15)."""
