"""Puerto: AuditoriaEtapaRepositoryPort -- Submodulos 9.10/9.15."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.auditoria_etapa import AuditoriaEtapa


class AuditoriaEtapaRepositoryPort(ABC):
    @abstractmethod
    def guardar_lote(self, etapas: list[AuditoriaEtapa]) -> list[AuditoriaEtapa]: ...

    @abstractmethod
    def listar_por_trabajo(self, trabajo_orquestador_id: str) -> list[AuditoriaEtapa]: ...

    @abstractmethod
    def listar_todo(self, limite: int = 5000) -> list[AuditoriaEtapa]:
        """Insumo del Motor de Estadisticas (Submodulo 9.12)."""
