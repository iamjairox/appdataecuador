"""Puerto: AlertaAcademicaRepositoryPort -- Submodulo 7.8."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from govdata.domain.entities.alerta_academica import AlertaAcademica


class AlertaAcademicaRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, alerta: AlertaAcademica) -> AlertaAcademica: ...

    @abstractmethod
    def guardar_lote(self, alertas: list[AlertaAcademica]) -> list[AlertaAcademica]: ...

    @abstractmethod
    def buscar_por_id(self, alerta_id: uuid.UUID) -> AlertaAcademica | None: ...

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaAcademica]: ...

    @abstractmethod
    def listar_pendientes(self, limite: int = 100) -> list[AlertaAcademica]:
        """Insumo del Programador de Enriquecimiento (Submodulo 7.20,
        mejora 2: "priorizar personas con alertas pendientes")."""
