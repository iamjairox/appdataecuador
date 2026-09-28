"""Puerto: VerificacionRepositoryPort -- Submodulos 5.10/5.15."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.verificacion import Verificacion


class VerificacionRepositoryPort(ABC):
    """Persistencia del historial de verificaciones (con o sin cambio detectado)."""

    @abstractmethod
    def registrar(self, verificacion: Verificacion) -> Verificacion: ...

    @abstractmethod
    def listar_por_entidad(self, entidad_id: int) -> list[Verificacion]:
        """Historial completo, mas antigua primero -- base del Timeline (5.13)."""

    @abstractmethod
    def buscar_ultima_por_entidad(self, entidad_id: int) -> Verificacion | None:
        """La verificacion mas reciente -- "¿cuando fue la ultima vez que
        se reviso esta entidad?", incluso si nunca hubo cambios."""
