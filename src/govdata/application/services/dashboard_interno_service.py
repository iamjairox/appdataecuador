"""Servicio: DashboardInternoService -- Submodulo 9.11 (Dashboard
interno, SOLO backend: "No interfaz grafica. Crear unicamente DTOs...
Sin API REST.")."""

from __future__ import annotations

from govdata.application.dto.dashboard_interno_dto import DashboardInternoDTO
from govdata.application.ports.trabajo_orquestador_repository_port import (
    TrabajoOrquestadorRepositoryPort,
)
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador


class DashboardInternoService:
    def __init__(self, repository: TrabajoOrquestadorRepositoryPort) -> None:
        self._repository = repository

    def construir(self) -> DashboardInternoDTO:
        conteos = self._repository.contar_por_estado()

        trabajos_activos = conteos.get(EstadoTrabajoOrquestador.EJECUTANDO, 0) + conteos.get(
            EstadoTrabajoOrquestador.REINTENTANDO, 0
        )
        trabajos_pendientes = (
            conteos.get(EstadoTrabajoOrquestador.PENDIENTE, 0)
            + conteos.get(EstadoTrabajoOrquestador.EN_COLA, 0)
            + conteos.get(EstadoTrabajoOrquestador.PAUSADO, 0)
        )
        completados = self._repository.listar_por_estado(EstadoTrabajoOrquestador.COMPLETADO, limite=5000)
        duraciones = [
            (t.finalizado_en - t.iniciado_en).total_seconds()
            for t in completados
            if t.iniciado_en is not None and t.finalizado_en is not None
        ]
        ultima_actualizacion = max((t.finalizado_en for t in completados if t.finalizado_en), default=None)

        return DashboardInternoDTO(
            trabajos_activos=trabajos_activos,
            trabajos_pendientes=trabajos_pendientes,
            trabajos_completados=conteos.get(EstadoTrabajoOrquestador.COMPLETADO, 0),
            tiempo_promedio_segundos=round(sum(duraciones) / len(duraciones), 4) if duraciones else 0.0,
            errores=conteos.get(EstadoTrabajoOrquestador.ERROR, 0),
            ultima_actualizacion=ultima_actualizacion,
            entidades_pendientes=trabajos_pendientes,
        )
