"""Servicio: OportunidadComercialService -- Submodulo 5.17 (preparacion
para un futuro CRM). Mismo patron que `AlertaService`: capa fina sobre
las reglas de dominio puras (`generador_eventos_negocio`)."""

from __future__ import annotations

from datetime import datetime

from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.application.ports.oportunidad_comercial_repository_port import (
    OportunidadComercialRepositoryPort,
)
from govdata.config.logging_config import get_logger
from govdata.domain.entities.oportunidad_comercial import OportunidadComercial
from govdata.domain.rules.generador_eventos_negocio import (
    generar_oportunidades_documento,
    generar_oportunidades_funcionario,
)
from govdata.domain.rules.reglas_configurables import ReglasCriticidad

logger = get_logger(__name__)


class OportunidadComercialService:
    def __init__(self, oportunidad_repository: OportunidadComercialRepositoryPort, reglas: ReglasCriticidad) -> None:
        self._oportunidad_repository = oportunidad_repository
        self._reglas = reglas

    def generar_y_guardar(
        self,
        diferencias: list[DiferenciaFuncionarioDTO],
        estadisticas: EstadisticasComparacionDTO,
        entidad_id: int,
        persona_id_por_fingerprint: dict[str, int],
        detectado_en: datetime,
    ) -> list[OportunidadComercial]:
        oportunidades: list[OportunidadComercial] = []
        for diferencia in diferencias:
            if not diferencia.es_cambio:
                continue
            persona_id = persona_id_por_fingerprint.get(diferencia.fingerprint)
            oportunidades.extend(generar_oportunidades_funcionario(diferencia, entidad_id, persona_id, detectado_en))

        oportunidades.extend(generar_oportunidades_documento(estadisticas, self._reglas, entidad_id, detectado_en))

        if not oportunidades:
            return []
        guardadas = self._oportunidad_repository.guardar_lote(oportunidades)
        logger.info("oportunidades_comerciales_generadas", entidad_id=entidad_id, cantidad=len(guardadas))
        return guardadas
