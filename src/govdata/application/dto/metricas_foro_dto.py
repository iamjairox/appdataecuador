"""DTO: MetricasForoDTO -- Submodulo 8.15 (Metricas)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricasForoDTO:
    tiempo_promedio_segundos: float
    errores: int
    cache_hit: int
    cache_miss: int
    cantidad_consultada: int
    cantidad_exitosa: int
    cantidad_con_error: int
