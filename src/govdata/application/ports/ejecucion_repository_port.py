"""Puerto: EjecucionRepositoryPort."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.ejecucion import Ejecucion


class EjecucionRepositoryPort(ABC):
    """Persistencia de la auditoria de ejecuciones del pipeline."""

    @abstractmethod
    def registrar(self, ejecucion: Ejecucion) -> Ejecucion:
        """Inserta un nuevo registro de auditoria (al iniciar una etapa)."""

    @abstractmethod
    def actualizar(self, ejecucion: Ejecucion) -> Ejecucion:
        """Actualiza un registro existente (al finalizar la etapa)."""
