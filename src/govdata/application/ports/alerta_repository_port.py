"""Puerto: AlertaRepositoryPort -- Submodulo 5.6."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from govdata.domain.entities.alerta import Alerta


class AlertaRepositoryPort(ABC):
    """Persistencia de Alertas Inteligentes."""

    @abstractmethod
    def guardar(self, alerta: Alerta) -> Alerta: ...

    @abstractmethod
    def guardar_lote(self, alertas: list[Alerta]) -> list[Alerta]: ...

    @abstractmethod
    def buscar_por_id(self, alerta_id: uuid.UUID) -> Alerta | None: ...

    @abstractmethod
    def listar_por_entidad(self, entidad_id: int) -> list[Alerta]: ...

    @abstractmethod
    def listar_por_documento(self, documento_id: int) -> list[Alerta]: ...
