"""DTO: AlertaForoDTO -- forma serializable de `AlertaForo` (Submodulo 8.7)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.alerta_foro import AlertaForo


@dataclass(frozen=True, slots=True)
class AlertaForoDTO:
    id: str
    persona_master_id: int
    tipo: str
    prioridad: str
    descripcion: str
    detectado_en: datetime
    estado: str
    registro_foro_id: int | None = None

    @classmethod
    def desde_entidad(cls, alerta: AlertaForo) -> AlertaForoDTO:
        return cls(
            id=str(alerta.id), persona_master_id=alerta.persona_master_id, tipo=alerta.tipo.value,
            prioridad=alerta.prioridad.value, descripcion=alerta.descripcion, detectado_en=alerta.detectado_en,
            estado=alerta.estado.value, registro_foro_id=alerta.registro_foro_id,
        )
