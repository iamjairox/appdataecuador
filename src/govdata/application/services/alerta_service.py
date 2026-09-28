"""Servicio: AlertaService -- Submodulo 5.6 (Alertas Inteligentes).

Capa fina sobre las reglas de dominio puras (`generador_alertas`): agrega
el `persona_id` ya resuelto (Submodulo 5.11) a cada diferencia, invoca las
reglas, y persiste el resultado. No decide POR SI MISMO que alertas
generar -- esa logica vive en el dominio para poder testearse sin base de
datos."""

from __future__ import annotations

from datetime import datetime

from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.application.ports.alerta_repository_port import AlertaRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.alerta import Alerta
from govdata.domain.rules.generador_alertas import (
    generar_alertas_documento,
    generar_alertas_funcionario,
)
from govdata.domain.rules.reglas_configurables import ReglasCriticidad

logger = get_logger(__name__)


class AlertaService:
    def __init__(self, alerta_repository: AlertaRepositoryPort, reglas: ReglasCriticidad) -> None:
        self._alerta_repository = alerta_repository
        self._reglas = reglas

    def generar_y_guardar(
        self,
        diferencias: list[DiferenciaFuncionarioDTO],
        estadisticas: EstadisticasComparacionDTO,
        entidad_id: int,
        documento_id: int,
        persona_id_por_fingerprint: dict[str, int],
        detectado_en: datetime,
    ) -> list[Alerta]:
        alertas: list[Alerta] = []
        for diferencia in diferencias:
            if not diferencia.es_cambio:
                continue
            persona_id = persona_id_por_fingerprint.get(diferencia.fingerprint)
            alertas.extend(
                generar_alertas_funcionario(diferencia, entidad_id, documento_id, persona_id, detectado_en)
            )

        alertas.extend(generar_alertas_documento(estadisticas, self._reglas, entidad_id, documento_id, detectado_en))

        if not alertas:
            return []
        guardadas = self._alerta_repository.guardar_lote(alertas)
        logger.info("alertas_generadas", entidad_id=entidad_id, documento_id=documento_id, cantidad=len(guardadas))
        return guardadas
