"""Puerto: ConsultaFuenteLogRepositoryPort -- Submodulo 6.10."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.consulta_fuente_log import ConsultaFuenteLog
from govdata.domain.value_objects.fuente_externa import FuenteExterna


class ConsultaFuenteLogRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, log: ConsultaFuenteLog) -> ConsultaFuenteLog: ...

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[ConsultaFuenteLog]: ...

    @abstractmethod
    def ultima_consulta(self, persona_master_id: int, fuente: FuenteExterna) -> ConsultaFuenteLog | None:
        """El intento mas reciente (exitoso o no) -- insumo del Cache por
        Fuente (Submodulo 6.8): "si hash igual + version igual + fecha
        vigente -> no volver a consultar"."""
