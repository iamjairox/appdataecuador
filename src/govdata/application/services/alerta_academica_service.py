"""Servicio: AlertaAcademicaService -- Submodulo 7.8."""

from __future__ import annotations

from govdata.application.ports.alerta_academica_repository_port import (
    AlertaAcademicaRepositoryPort,
)
from govdata.config.logging_config import get_logger
from govdata.domain.entities.alerta_academica import AlertaAcademica

logger = get_logger(__name__)


class AlertaAcademicaService:
    def __init__(self, alerta_repository: AlertaAcademicaRepositoryPort) -> None:
        self._repository = alerta_repository

    def guardar_lote(self, alertas: list[AlertaAcademica]) -> list[AlertaAcademica]:
        if not alertas:
            return []
        guardadas = self._repository.guardar_lote(alertas)
        logger.info("alertas_academicas_creadas", cantidad=len(guardadas))
        return guardadas

    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaAcademica]:
        return self._repository.listar_por_persona_master(persona_master_id)

    def listar_pendientes(self, limite: int = 100) -> list[AlertaAcademica]:
        return self._repository.listar_pendientes(limite)
