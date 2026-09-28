"""Servicio: MetricasForoService -- Submodulo 8.15 (Metricas: "Tiempo
promedio. Errores. Hit Cache. Miss Cache. Cantidad consultada. Cantidad
exitosa. Cantidad con error.").

`errores` es el total de reintentos/errores transitorios absorbidos
(suma de `reintentos` de cada consulta, mismo criterio que Modulo 7),
distinto de `cantidad_con_error` (cuantas consultas terminaron fallidas
pese a los reintentos)."""

from __future__ import annotations

from govdata.application.dto.metricas_foro_dto import MetricasForoDTO
from govdata.application.ports.consulta_foro_repository_port import ConsultaForoRepositoryPort


class MetricasForoService:
    def __init__(self, consulta_repository: ConsultaForoRepositoryPort) -> None:
        self._consulta_repository = consulta_repository

    def calcular(self) -> MetricasForoDTO:
        consultas = self._consulta_repository.listar_todas()
        duraciones = [c.duracion_segundos for c in consultas if c.duracion_segundos is not None]
        exitosas = [c for c in consultas if c.exito is True]
        fallidas = [c for c in consultas if c.exito is False]
        cache_hit = len([c for c in consultas if c.cache_utilizado])
        cache_miss = len(consultas) - cache_hit
        errores_totales = sum(c.reintentos for c in consultas)

        return MetricasForoDTO(
            tiempo_promedio_segundos=round(sum(duraciones) / len(duraciones), 4) if duraciones else 0.0,
            errores=errores_totales,
            cache_hit=cache_hit,
            cache_miss=cache_miss,
            cantidad_consultada=len(consultas),
            cantidad_exitosa=len(exitosas),
            cantidad_con_error=len(fallidas),
        )
