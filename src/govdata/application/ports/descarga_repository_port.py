"""Puerto: DescargaRepositoryPort."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.descarga import Descarga


class DescargaRepositoryPort(ABC):
    """Persistencia del historial (append-only) de intentos de descarga."""

    @abstractmethod
    def registrar(self, descarga: Descarga) -> Descarga: ...

    @abstractmethod
    def listar_por_documento(self, documento_id: int) -> list[Descarga]:
        """Historial completo de intentos de un documento, mas reciente primero."""

    @abstractmethod
    def contar_intentos(self, documento_id: int) -> int:
        """Cuantos intentos (exitosos o no) ya se registraron para este
        documento -- determina el numero de intento del proximo y si se
        agoto el presupuesto de reintentos configurado."""
