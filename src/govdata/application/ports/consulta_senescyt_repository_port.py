"""Puerto: ConsultaSenescytRepositoryPort -- Submodulo 7.15."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from govdata.domain.entities.consulta_senescyt import ConsultaSenescyt


class ConsultaSenescytRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, consulta: ConsultaSenescyt) -> ConsultaSenescyt: ...

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[ConsultaSenescyt]: ...

    @abstractmethod
    def ultima_consulta(self, persona_master_id: int) -> ConsultaSenescyt | None:
        """El intento mas reciente (exitoso o no) -- insumo del Cache por
        Persona (Submodulo 7.10)."""

    @abstractmethod
    def listar_todas(self, desde: datetime | None = None) -> list[ConsultaSenescyt]:
        """Todas las consultas (opcionalmente desde una fecha) -- insumo
        de las Metricas (Submodulo 7.18)."""
