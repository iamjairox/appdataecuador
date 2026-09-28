"""Servicio: AlertaForoService -- Submodulo 8.7."""

from __future__ import annotations

from govdata.application.ports.alerta_foro_repository_port import AlertaForoRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.alerta_foro import AlertaForo

logger = get_logger(__name__)


class AlertaForoService:
    def __init__(self, alerta_repository: AlertaForoRepositoryPort) -> None:
        self._repository = alerta_repository

    def guardar_lote(self, alertas: list[AlertaForo]) -> list[AlertaForo]:
        if not alertas:
            return []
        guardadas = self._repository.guardar_lote(alertas)
        logger.info("alertas_foro_creadas", cantidad=len(guardadas))
        return guardadas

    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaForo]:
        return self._repository.listar_por_persona_master(persona_master_id)

    def listar_pendientes(self, limite: int = 100) -> list[AlertaForo]:
        return self._repository.listar_pendientes(limite)
