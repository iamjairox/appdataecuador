"""Puerto: CasoRevisionIdentidadRepositoryPort -- Submodulo 6.21."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad


class CasoRevisionIdentidadRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, caso: CasoRevisionIdentidad) -> CasoRevisionIdentidad: ...

    @abstractmethod
    def buscar_por_id(self, caso_id: uuid.UUID) -> CasoRevisionIdentidad | None: ...

    @abstractmethod
    def listar_pendientes(self, limite: int = 100) -> list[CasoRevisionIdentidad]:
        """Cola de revision manual -- insumo de un futuro dashboard
        administrativo (fuera de alcance del Modulo 6)."""

    @abstractmethod
    def buscar_pendiente_entre(
        self, persona_master_id_a: int, persona_master_id_b: int
    ) -> CasoRevisionIdentidad | None:
        """Evita crear casos duplicados para el mismo par de candidatas
        mientras el primero sigue PENDIENTE_REVISION."""
