"""DTO: EventoAcademicoDTO -- forma serializable de `EventoAcademico`
(Submodulo 7.9)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from govdata.domain.entities.evento_academico import EventoAcademico


@dataclass(frozen=True, slots=True)
class EventoAcademicoDTO:
    id: str
    tipo: str
    persona_master_id: int
    payload: dict[str, Any]
    estado: str
    creado_en: datetime
    consumido_en: datetime | None = None
    procesado_en: datetime | None = None

    @classmethod
    def desde_entidad(cls, evento: EventoAcademico) -> EventoAcademicoDTO:
        return cls(
            id=str(evento.id), tipo=evento.tipo.value, persona_master_id=evento.persona_master_id,
            payload=evento.payload, estado=evento.estado.value, creado_en=evento.creado_en,
            consumido_en=evento.consumido_en, procesado_en=evento.procesado_en,
        )
