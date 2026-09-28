"""DTO: TrabajoOrquestadorDTO -- forma serializable de `TrabajoOrquestador`
(Submodulo 9.6)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from govdata.domain.entities.trabajo_orquestador import TrabajoOrquestador


@dataclass(frozen=True, slots=True)
class TrabajoOrquestadorDTO:
    id: str
    tipo: str
    estado: str
    prioridad: str
    politica: str
    parametros: dict[str, Any]
    version_lock: int
    intentos: int
    max_intentos: int
    entidad_id: int | None
    creado_en: datetime | None
    actualizado_en: datetime | None
    iniciado_en: datetime | None
    finalizado_en: datetime | None
    ultimo_error: str | None

    @classmethod
    def desde_entidad(cls, trabajo: TrabajoOrquestador) -> TrabajoOrquestadorDTO:
        return cls(
            id=str(trabajo.id), tipo=trabajo.tipo.value, estado=trabajo.estado.value,
            prioridad=trabajo.prioridad.value, politica=trabajo.politica, parametros=trabajo.parametros,
            version_lock=trabajo.version_lock, intentos=trabajo.intentos, max_intentos=trabajo.max_intentos,
            entidad_id=trabajo.entidad_id, creado_en=trabajo.creado_en, actualizado_en=trabajo.actualizado_en,
            iniciado_en=trabajo.iniciado_en, finalizado_en=trabajo.finalizado_en, ultimo_error=trabajo.ultimo_error,
        )
