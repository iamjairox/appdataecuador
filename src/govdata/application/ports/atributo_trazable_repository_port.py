"""Puerto: AtributoTrazableRepositoryPort -- Submodulo 6.15 (Trazabilidad)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.atributo_trazable import AtributoTrazable


class AtributoTrazableRepositoryPort(ABC):
    @abstractmethod
    def guardar_lote(self, atributos: list[AtributoTrazable]) -> list[AtributoTrazable]:
        """Los atributos trazables NUNCA se actualizan ni se borran --
        siempre se agregan (son la evidencia de procedencia de cada dato)."""

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[AtributoTrazable]:
        """Todos los atributos (todas las fuentes, todas las versiones) --
        insumo del Motor de Fusion (Submodulo 6.14)."""
