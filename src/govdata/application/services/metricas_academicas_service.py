"""Servicio: MetricasAcademicasService -- Submodulo 7.18 (Metricas)."""

from __future__ import annotations

from govdata.application.dto.metricas_academicas_dto import MetricasAcademicasDTO
from govdata.application.ports.consulta_senescyt_repository_port import (
    ConsultaSenescytRepositoryPort,
)
from govdata.application.ports.historial_academico_repository_port import (
    HistorialAcademicoRepositoryPort,
)
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico


class MetricasAcademicasService:
    def __init__(
        self,
        consulta_repository: ConsultaSenescytRepositoryPort,
        historial_repository: HistorialAcademicoRepositoryPort,
    ) -> None:
        self._consulta_repository = consulta_repository
        self._historial_repository = historial_repository

    def calcular(self) -> MetricasAcademicasDTO:
        consultas = self._consulta_repository.listar_todas()
        duraciones = [c.duracion_segundos for c in consultas if c.duracion_segundos is not None]
        exitosas = [c for c in consultas if c.exito is True]
        fallidas = [c for c in consultas if c.exito is False]
        cache_hit = len([c for c in consultas if c.cache_utilizado])
        cache_miss = len(consultas) - cache_hit
        reintentos_totales = sum(c.reintentos for c in consultas)

        historial = self._historial_repository.listar_todo()
        titulos_nuevos = len([h for h in historial if h.tipo_cambio == TipoCambioAcademico.TITULO_NUEVO])

        return MetricasAcademicasDTO(
            tiempo_promedio_segundos=round(sum(duraciones) / len(duraciones), 4) if duraciones else 0.0,
            tiempo_maximo_segundos=round(max(duraciones), 4) if duraciones else 0.0,
            tiempo_minimo_segundos=round(min(duraciones), 4) if duraciones else 0.0,
            consultas_exitosas=len(exitosas),
            consultas_fallidas=len(fallidas),
            cache_hit=cache_hit,
            cache_miss=cache_miss,
            reintentos=reintentos_totales,
            cambios_detectados=len(historial),
            titulos_nuevos=titulos_nuevos,
        )
