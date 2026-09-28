"""DTO: ConsultaFuenteLogDTO -- forma serializable de `ConsultaFuenteLog`
(Submodulo 6.10)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.consulta_fuente_log import ConsultaFuenteLog


@dataclass(frozen=True, slots=True)
class ConsultaFuenteLogDTO:
    persona_master_id: int
    fuente: str
    iniciado_en: datetime
    id: int | None = None
    finalizado_en: datetime | None = None
    exito: bool | None = None
    duracion_segundos: float | None = None
    reintentos: int = 0
    error: str | None = None

    @classmethod
    def desde_entidad(cls, log: ConsultaFuenteLog) -> ConsultaFuenteLogDTO:
        return cls(
            id=log.id,
            persona_master_id=log.persona_master_id,
            fuente=log.fuente.value,
            iniciado_en=log.iniciado_en,
            finalizado_en=log.finalizado_en,
            exito=log.exito,
            duracion_segundos=log.duracion_segundos,
            reintentos=log.reintentos,
            error=log.error,
        )
