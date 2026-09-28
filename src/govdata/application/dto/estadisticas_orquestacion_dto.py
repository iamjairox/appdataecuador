"""DTO: EstadisticasOrquestacionDTO -- Submodulo 9.12 (Motor de
Estadisticas)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EstadisticasOrquestacionDTO:
    funcionarios_encontrados: int = 0
    funcionarios_juridicos: int = 0
    consultas_senescyt: int = 0
    consultas_foro: int = 0
    cambios_detectados: int = 0
    alertas: int = 0
    errores: int = 0
    cache_hit: int = 0
    cache_miss: int = 0
