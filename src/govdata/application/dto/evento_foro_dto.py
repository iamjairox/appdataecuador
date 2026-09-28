"""DTO: EventoForoDTO -- forma serializable de `EventoForo` (Submodulo 8.7)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from govdata.domain.entities.evento_foro import EventoForo


@dataclass(frozen=True, slots=True)
class EventoForoDTO:
    id: str
    tipo: str
    persona_master_id: int
    payload: dict[str, Any]
    estado: str
    creado_en: datetime
    consumido_en: datetime | None = None
    procesado_en: datetime | None = None

    @classmethod
    def desde_entidad(cls, evento: EventoForo) -> EventoForoDTO:
        return cls(
            id=str(evento.id), tipo=evento.tipo.value, persona_master_id=evento.persona_master_id,
            payload=evento.payload, estado=evento.estado.value, creado_en=evento.creado_en,
            consumido_en=evento.consumido_en, procesado_en=evento.procesado_en,
        )
