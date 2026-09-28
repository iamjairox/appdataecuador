"""DTO: MetricasAcademicasDTO -- Submodulo 7.18 (Metricas)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricasAcademicasDTO:
    tiempo_promedio_segundos: float
    tiempo_maximo_segundos: float
    tiempo_minimo_segundos: float
    consultas_exitosas: int
    consultas_fallidas: int
    cache_hit: int
    cache_miss: int
    reintentos: int
    cambios_detectados: int
    titulos_nuevos: int
