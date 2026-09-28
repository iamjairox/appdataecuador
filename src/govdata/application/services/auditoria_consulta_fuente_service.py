"""Servicio: AuditoriaConsultaFuenteService -- Submodulo 6.10 (Historial
de Consultas)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from govdata.application.ports.consulta_fuente_log_repository_port import (
    ConsultaFuenteLogRepositoryPort,
)
from govdata.domain.entities.consulta_fuente_log import ConsultaFuenteLog
from govdata.domain.value_objects.fuente_externa import FuenteExterna


class AuditoriaConsultaFuenteService:
    def __init__(
        self,
        consulta_fuente_log_repository: ConsultaFuenteLogRepositoryPort,
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = consulta_fuente_log_repository
        self._ahora_provider = ahora_provider

    def iniciar(self, persona_master_id: int, fuente: FuenteExterna) -> ConsultaFuenteLog:
        log = ConsultaFuenteLog(
            persona_master_id=persona_master_id, fuente=fuente, iniciado_en=self._ahora_provider()
        )
        return self._repository.guardar(log)

    def finalizar(
        self, log: ConsultaFuenteLog, exito: bool, error: str | None = None
    ) -> ConsultaFuenteLog:
        cuando = self._ahora_provider()
        duracion = (cuando - log.iniciado_en).total_seconds()
        log.finalizar(exito=exito, cuando=cuando, duracion_segundos=duracion, error=error)
        return self._repository.guardar(log)

    def registrar_reintento(self, log: ConsultaFuenteLog) -> None:
        log.reintentos += 1
