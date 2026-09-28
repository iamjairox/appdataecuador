"""DTO: AuditoriaEtapaDTO -- forma serializable de `AuditoriaEtapa`
(Submodulos 9.10/9.15)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.auditoria_etapa import AuditoriaEtapa


@dataclass(frozen=True, slots=True)
class AuditoriaEtapaDTO:
    id: int | None
    trabajo_orquestador_id: str
    tipo_paso: str
    estado_paso: str
    iniciado_en: datetime
    finalizado_en: datetime | None
    duracion_segundos: float | None
    razon_omision: str | None
    cantidad_registros: int
    error: str | None
    cache_utilizada: bool
    version_utilizada: str | None

    @classmethod
    def desde_entidad(cls, etapa: AuditoriaEtapa) -> AuditoriaEtapaDTO:
        return cls(
            id=etapa.id, trabajo_orquestador_id=etapa.trabajo_orquestador_id, tipo_paso=etapa.tipo_paso.value,
            estado_paso=etapa.estado_paso.value, iniciado_en=etapa.iniciado_en, finalizado_en=etapa.finalizado_en,
            duracion_segundos=etapa.duracion_segundos, razon_omision=etapa.razon_omision,
            cantidad_registros=etapa.cantidad_registros, error=etapa.error, cache_utilizada=etapa.cache_utilizada,
            version_utilizada=etapa.version_utilizada,
        )
