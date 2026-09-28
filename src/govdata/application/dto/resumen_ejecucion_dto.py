"""DTO: ResumenEjecucionPipelineDTO."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ResumenEjecucionPipelineDTO:
    """Metricas agregadas de una corrida completa del pipeline de descubrimiento."""

    total_entidades: int
    publicaciones_encontradas: int
    documentos_encontrados: int
    errores: int
    iniciado_en: datetime
    finalizado_en: datetime

    @property
    def duracion_segundos(self) -> float:
        return (self.finalizado_en - self.iniciado_en).total_seconds()
