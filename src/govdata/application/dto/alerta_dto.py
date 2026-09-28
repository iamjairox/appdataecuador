"""DTO: AlertaDTO -- forma serializable de `Alerta` (Submodulo 5.6).

Separada de la entidad de dominio `Alerta` por el mismo motivo que
`FuncionarioUnificadoDTO` esta separado de `Funcionario` (Modulo 4): el
DTO es la capa de PRESENTACION (UUID como `str`, enums como `str`, lista
plana), la entidad es el modelo de dominio con sus invariantes y
transiciones de estado.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.alerta import Alerta


@dataclass(frozen=True, slots=True)
class AlertaDTO:
    id: str
    entidad_id: int
    tipo: str
    prioridad: str
    descripcion: str
    detectado_en: datetime
    estado: str
    persona_id: int | None = None
    documento_id: int | None = None

    @classmethod
    def desde_entidad(cls, alerta: Alerta) -> AlertaDTO:
        return cls(
            id=str(alerta.id),
            entidad_id=alerta.entidad_id,
            tipo=alerta.tipo.value,
            prioridad=alerta.prioridad.value,
            descripcion=alerta.descripcion,
            detectado_en=alerta.detectado_en,
            estado=alerta.estado.value,
            persona_id=alerta.persona_id,
            documento_id=alerta.documento_id,
        )
