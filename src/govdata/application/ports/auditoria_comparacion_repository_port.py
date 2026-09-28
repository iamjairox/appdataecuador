"""Puerto: AuditoriaComparacionRepositoryPort -- Submodulo 5.9."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.auditoria_comparacion import AuditoriaComparacion


class AuditoriaComparacionRepositoryPort(ABC):
    """Persistencia de la auditoria de cada ejecucion del Motor de Comparacion."""

    @abstractmethod
    def registrar(self, auditoria: AuditoriaComparacion) -> AuditoriaComparacion: ...

    @abstractmethod
    def listar_por_documento(self, documento_id: int) -> list[AuditoriaComparacion]: ...
