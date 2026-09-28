"""Servicio: AuditoriaComparacionService -- Submodulo 5.9.

Registra cada ejecucion del Motor de Comparacion: quien la ejecuto, sobre
que documento y version, cuando, cuanto tardo, y cuantos cambios detecto
(o el error, si fallo). Simetrico a `JobManagerService` (Modulo 4)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from govdata.application.ports.auditoria_comparacion_repository_port import (
    AuditoriaComparacionRepositoryPort,
)
from govdata.config.logging_config import get_logger
from govdata.domain.entities.auditoria_comparacion import AuditoriaComparacion

logger = get_logger(__name__)


class AuditoriaComparacionService:
    def __init__(
        self,
        auditoria_repository: AuditoriaComparacionRepositoryPort,
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._auditoria_repository = auditoria_repository
        self._ahora = ahora_provider

    def iniciar(
        self, entidad_id: int, documento_id: int, version_documento: int, ejecutado_por: str = "sistema"
    ) -> AuditoriaComparacion:
        auditoria = AuditoriaComparacion(
            entidad_id=entidad_id,
            documento_id=documento_id,
            version_documento=version_documento,
            ejecutado_por=ejecutado_por,
            iniciado_en=self._ahora(),
        )
        registrada = self._auditoria_repository.registrar(auditoria)
        logger.info("auditoria_comparacion_iniciada", entidad_id=entidad_id, documento_id=documento_id)
        return registrada

    def finalizar(self, auditoria: AuditoriaComparacion, cambios_detectados: int) -> AuditoriaComparacion:
        auditoria.finalizar(self._ahora(), cambios_detectados)
        registrada = self._auditoria_repository.registrar(auditoria)
        logger.info(
            "auditoria_comparacion_finalizada",
            entidad_id=auditoria.entidad_id,
            documento_id=auditoria.documento_id,
            cambios_detectados=cambios_detectados,
            duracion_segundos=auditoria.duracion_segundos,
        )
        return registrada

    def marcar_error(self, auditoria: AuditoriaComparacion, mensaje: str) -> AuditoriaComparacion:
        auditoria.marcar_error(mensaje, self._ahora())
        registrada = self._auditoria_repository.registrar(auditoria)
        logger.warning(
            "auditoria_comparacion_con_error", entidad_id=auditoria.entidad_id, documento_id=auditoria.documento_id, error=mensaje
        )
        return registrada
