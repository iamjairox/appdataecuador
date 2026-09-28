"""Puerto: AlertaPerfilRepositoryPort -- Submodulo 6.13."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from govdata.domain.entities.alerta_perfil import AlertaPerfil


class AlertaPerfilRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, alerta: AlertaPerfil) -> AlertaPerfil: ...

    @abstractmethod
    def guardar_lote(self, alertas: list[AlertaPerfil]) -> list[AlertaPerfil]: ...

    @abstractmethod
    def buscar_por_id(self, alerta_id: uuid.UUID) -> AlertaPerfil | None: ...

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaPerfil]: ...
