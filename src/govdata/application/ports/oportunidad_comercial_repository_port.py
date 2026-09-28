"""Puerto: OportunidadComercialRepositoryPort -- Submodulo 5.17."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.oportunidad_comercial import OportunidadComercial


class OportunidadComercialRepositoryPort(ABC):
    """Persistencia de eventos de negocio (preparacion para un futuro CRM)."""

    @abstractmethod
    def guardar(self, oportunidad: OportunidadComercial) -> OportunidadComercial: ...

    @abstractmethod
    def guardar_lote(self, oportunidades: list[OportunidadComercial]) -> list[OportunidadComercial]: ...

    @abstractmethod
    def listar_por_entidad(self, entidad_id: int) -> list[OportunidadComercial]: ...
