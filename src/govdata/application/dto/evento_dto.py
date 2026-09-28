"""DTO: EventoDTO -- forma serializable de `Evento` (Submodulo 5.7)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.evento import Evento


@dataclass(frozen=True, slots=True)
class EventoDTO:
    id: str
    tipo: str
    entidad_id: int
    referencia_id: str
    payload: dict
    estado: str
    creado_en: datetime
    consumido_en: datetime | None = None
    procesado_en: datetime | None = None

    @classmethod
    def desde_entidad(cls, evento: Evento) -> EventoDTO:
        return cls(
            id=str(evento.id),
            tipo=evento.tipo.value,
            entidad_id=evento.entidad_id,
            referencia_id=str(evento.referencia_id),
            payload=evento.payload,
            estado=evento.estado.value,
            creado_en=evento.creado_en,
            consumido_en=evento.consumido_en,
            procesado_en=evento.procesado_en,
        )
