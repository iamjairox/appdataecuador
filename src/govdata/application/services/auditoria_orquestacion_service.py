"""Servicio: AuditoriaOrquestacionService -- Submodulos 9.10 (Monitoreo:
inicio/fin/duracion/errores/cantidad de registros) + 9.15 (Auditoria
completa: modulo ejecutado/omitido/razon/cache/version/tiempo).

Un unico servicio para los dos submodulos -- ambos piden exactamente el
mismo dato por paso, ver `AuditoriaEtapa` para la justificacion completa."""

from __future__ import annotations

from datetime import datetime

from govdata.application.dto.auditoria_etapa_dto import AuditoriaEtapaDTO
from govdata.application.ports.auditoria_etapa_repository_port import AuditoriaEtapaRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.auditoria_etapa import AuditoriaEtapa
from govdata.domain.value_objects.estado_paso import EstadoPaso
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline

logger = get_logger(__name__)


class AuditoriaOrquestacionService:
    def __init__(self, repository: AuditoriaEtapaRepositoryPort) -> None:
        self._repository = repository

    def registrar_ejecutado(
        self, trabajo_orquestador_id: str, tipo_paso: TipoPasoPipeline, iniciado_en: datetime, finalizado_en: datetime,
        cantidad_registros: int = 0, cache_utilizada: bool = False, version_utilizada: str | None = None,
    ) -> AuditoriaEtapa:
        return self._guardar(
            AuditoriaEtapa(
                trabajo_orquestador_id=trabajo_orquestador_id, tipo_paso=tipo_paso, estado_paso=EstadoPaso.EJECUTADO,
                iniciado_en=iniciado_en, finalizado_en=finalizado_en, cantidad_registros=cantidad_registros,
                cache_utilizada=cache_utilizada, version_utilizada=version_utilizada,
            )
        )

    def registrar_omitido(
        self, trabajo_orquestador_id: str, tipo_paso: TipoPasoPipeline, razon_omision: str, cuando: datetime,
    ) -> AuditoriaEtapa:
        return self._guardar(
            AuditoriaEtapa(
                trabajo_orquestador_id=trabajo_orquestador_id, tipo_paso=tipo_paso, estado_paso=EstadoPaso.OMITIDO,
                iniciado_en=cuando, finalizado_en=cuando, razon_omision=razon_omision,
            )
        )

    def registrar_fallido(
        self, trabajo_orquestador_id: str, tipo_paso: TipoPasoPipeline, error: str, iniciado_en: datetime,
        finalizado_en: datetime,
    ) -> AuditoriaEtapa:
        return self._guardar(
            AuditoriaEtapa(
                trabajo_orquestador_id=trabajo_orquestador_id, tipo_paso=tipo_paso, estado_paso=EstadoPaso.FALLIDO,
                iniciado_en=iniciado_en, finalizado_en=finalizado_en, error=error,
            )
        )

    def _guardar(self, etapa: AuditoriaEtapa) -> AuditoriaEtapa:
        guardadas = self._repository.guardar_lote([etapa])
        logger.info(
            "auditoria_etapa_registrada", trabajo_orquestador_id=etapa.trabajo_orquestador_id,
            tipo_paso=etapa.tipo_paso.value, estado_paso=etapa.estado_paso.value,
        )
        return guardadas[0]

    def listar_por_trabajo(self, trabajo_orquestador_id: str) -> list[AuditoriaEtapaDTO]:
        return [AuditoriaEtapaDTO.desde_entidad(e) for e in self._repository.listar_por_trabajo(trabajo_orquestador_id)]
