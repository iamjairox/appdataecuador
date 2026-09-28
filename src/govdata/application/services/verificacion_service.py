"""Servicio: VerificacionService -- Submodulos 5.10 (Cache Inteligente de
comparacion) y 5.15 (registro de verificaciones del Motor de Monitoreo
Continuo).

"Mantener un historial de verificaciones, incluso cuando no haya
cambios" -- instruccion explicita del cliente. Cada llamada de
`MonitoreoContinuoService` a una entidad, tenga o no cambios reales,
termina registrando UNA `Verificacion`."""

from __future__ import annotations

from datetime import datetime

from govdata.application.ports.verificacion_repository_port import VerificacionRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.verificacion import Verificacion

logger = get_logger(__name__)


class VerificacionService:
    def __init__(self, verificacion_repository: VerificacionRepositoryPort) -> None:
        self._verificacion_repository = verificacion_repository

    def registrar(
        self,
        entidad_id: int,
        hubo_cambio: bool,
        motivo: str,
        verificado_en: datetime,
        documento_id: int | None = None,
        hash_verificado: str | None = None,
    ) -> Verificacion:
        verificacion = Verificacion(
            entidad_id=entidad_id,
            hubo_cambio=hubo_cambio,
            motivo=motivo,
            verificado_en=verificado_en,
            documento_id=documento_id,
            hash_verificado=hash_verificado,
        )
        registrada = self._verificacion_repository.registrar(verificacion)
        logger.info("verificacion_registrada", entidad_id=entidad_id, hubo_cambio=hubo_cambio, motivo=motivo)
        return registrada

    def ultima_verificacion(self, entidad_id: int) -> Verificacion | None:
        return self._verificacion_repository.buscar_ultima_por_entidad(entidad_id)
