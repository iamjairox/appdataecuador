"""DTO: OportunidadComercialDTO -- forma serializable de `OportunidadComercial`
(Submodulo 5.17)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.oportunidad_comercial import OportunidadComercial


@dataclass(frozen=True, slots=True)
class OportunidadComercialDTO:
    id: str
    entidad_id: int
    tipo: str
    descripcion: str
    detectado_en: datetime
    prioridad: str
    persona_id: int | None = None

    @classmethod
    def desde_entidad(cls, oportunidad: OportunidadComercial) -> OportunidadComercialDTO:
        return cls(
            id=str(oportunidad.id),
            entidad_id=oportunidad.entidad_id,
            tipo=oportunidad.tipo.value,
            descripcion=oportunidad.descripcion,
            detectado_en=oportunidad.detectado_en,
            prioridad=oportunidad.prioridad.value,
            persona_id=oportunidad.persona_id,
        )
