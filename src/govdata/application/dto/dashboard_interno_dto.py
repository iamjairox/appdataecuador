"""DTO: DashboardInternoDTO -- Submodulo 9.11 (Dashboard interno, SOLO
backend: "No interfaz grafica. Crear unicamente DTOs... Sin API REST.")."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DashboardInternoDTO:
    trabajos_activos: int
    trabajos_pendientes: int
    trabajos_completados: int
    tiempo_promedio_segundos: float
    errores: int
    ultima_actualizacion: datetime | None
    entidades_pendientes: int
