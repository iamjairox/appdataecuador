"""DTO: AlertaAcademicaDTO -- forma serializable de `AlertaAcademica`
(Submodulo 7.8)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.alerta_academica import AlertaAcademica


@dataclass(frozen=True, slots=True)
class AlertaAcademicaDTO:
    id: str
    persona_master_id: int
    tipo: str
    prioridad: str
    descripcion: str
    detectado_en: datetime
    estado: str
    titulo_academico_id: int | None = None

    @classmethod
    def desde_entidad(cls, alerta: AlertaAcademica) -> AlertaAcademicaDTO:
        return cls(
            id=str(alerta.id), persona_master_id=alerta.persona_master_id, tipo=alerta.tipo.value,
            prioridad=alerta.prioridad.value, descripcion=alerta.descripcion, detectado_en=alerta.detectado_en,
            estado=alerta.estado.value, titulo_academico_id=alerta.titulo_academico_id,
        )
