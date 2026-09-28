"""Puerto: RegistroFuenteRepositoryPort -- Submodulo 6.9 (Versionado por
Fuente)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.registro_fuente import RegistroFuente
from govdata.domain.value_objects.fuente_externa import FuenteExterna


class RegistroFuenteRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, registro: RegistroFuente) -> RegistroFuente:
        """Inserta una version NUEVA. Nunca actualiza `datos` de una
        version existente -- versionar es siempre agregar, jamas
        sobreescribir (Submodulo 6.9)."""

    @abstractmethod
    def buscar_vigente(self, persona_master_id: int, fuente: FuenteExterna) -> RegistroFuente | None:
        """La version `vigente=True` mas reciente para esa PersonaMaster+
        fuente, o None si nunca se consulto esa fuente."""

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[RegistroFuente]:
        """Todas las versiones, de todas las fuentes -- insumo de
        `TimelinePersonaService` (Submodulo 6.5) y del contrato oficial
        (`fuentes`, Submodulo 6.16)."""

    @abstractmethod
    def listar_historial(self, persona_master_id: int, fuente: FuenteExterna) -> list[RegistroFuente]:
        """Todas las versiones de UNA fuente, en orden -- Persona -> SENESCYT
        -> Version 1 -> Version 2 -> Version 3."""
