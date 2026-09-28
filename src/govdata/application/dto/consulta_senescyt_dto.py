"""DTO: ConsultaSenescytDTO -- forma serializable de `ConsultaSenescyt`
(Submodulo 7.15)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from govdata.domain.entities.consulta_senescyt import ConsultaSenescyt


@dataclass(frozen=True, slots=True)
class ConsultaSenescytDTO:
    persona_master_id: int
    iniciado_en: datetime
    id: int | None = None
    finalizado_en: datetime | None = None
    exito: bool | None = None
    duracion_segundos: float | None = None
    error: str | None = None
    reintentos: int = 0
    cache_utilizado: bool = False
    version_resultante: int | None = None
    respuesta_cruda: dict[str, Any] | None = None

    @classmethod
    def desde_entidad(cls, consulta: ConsultaSenescyt) -> ConsultaSenescytDTO:
        return cls(
            id=consulta.id, persona_master_id=consulta.persona_master_id, iniciado_en=consulta.iniciado_en,
            finalizado_en=consulta.finalizado_en, exito=consulta.exito,
            duracion_segundos=consulta.duracion_segundos, error=consulta.error, reintentos=consulta.reintentos,
            cache_utilizado=consulta.cache_utilizado, version_resultante=consulta.version_resultante,
            respuesta_cruda=consulta.respuesta_cruda,
        )
