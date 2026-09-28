"""DTO: ResumenDescargaDTO."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ResumenDescargaDTO:
    """Metricas agregadas de una corrida del orquestador de descargas."""

    total_documentos: int
    descargados: int
    omitidos: int
    errores: int
    bytes_totales: int
    iniciado_en: datetime
    finalizado_en: datetime

    @property
    def duracion_segundos(self) -> float:
        return (self.finalizado_en - self.iniciado_en).total_seconds()

    @property
    def velocidad_promedio_bytes_por_segundo(self) -> float:
        duracion = max(self.duracion_segundos, 1e-6)
        return self.bytes_totales / duracion
