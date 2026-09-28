"""DTO: AlertaPerfilDTO -- forma serializable de `AlertaPerfil`
(Submodulo 6.13)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.alerta_perfil import AlertaPerfil


@dataclass(frozen=True, slots=True)
class AlertaPerfilDTO:
    id: str
    persona_master_id: int
    tipo: str
    prioridad: str
    descripcion: str
    detectado_en: datetime
    estado: str
    registro_fuente_id: int | None = None

    @classmethod
    def desde_entidad(cls, alerta: AlertaPerfil) -> AlertaPerfilDTO:
        return cls(
            id=str(alerta.id),
            persona_master_id=alerta.persona_master_id,
            tipo=alerta.tipo.value,
            prioridad=alerta.prioridad.value,
            descripcion=alerta.descripcion,
            detectado_en=alerta.detectado_en,
            estado=alerta.estado.value,
            registro_fuente_id=alerta.registro_fuente_id,
        )
