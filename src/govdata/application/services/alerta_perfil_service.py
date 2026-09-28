"""Servicio: AlertaPerfilService -- Submodulo 6.13."""

from __future__ import annotations

from govdata.application.ports.alerta_perfil_repository_port import AlertaPerfilRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.alerta_perfil import AlertaPerfil

logger = get_logger(__name__)


class AlertaPerfilService:
    def __init__(self, alerta_perfil_repository: AlertaPerfilRepositoryPort) -> None:
        self._repository = alerta_perfil_repository

    def guardar_lote(self, alertas: list[AlertaPerfil]) -> list[AlertaPerfil]:
        if not alertas:
            return []
        guardadas = self._repository.guardar_lote(alertas)
        logger.info("alertas_perfil_creadas", cantidad=len(guardadas))
        return guardadas

    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaPerfil]:
        return self._repository.listar_por_persona_master(persona_master_id)
