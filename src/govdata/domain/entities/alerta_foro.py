"""Entidad de dominio: AlertaForo -- Submodulo 8.7 (Motor de Alertas)."""

from __future__ import annotations

import uuid as uuid_module
from dataclasses import dataclass, field
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import AlertaForoInvalidaError
from govdata.domain.value_objects.estado_alerta_foro import EstadoAlertaForo
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_foro import TipoAlertaForo


@dataclass(slots=True)
class AlertaForo:
    persona_master_id: int
    tipo: TipoAlertaForo
    prioridad: NivelCriticidad
    descripcion: str
    detectado_en: datetime
    id: uuid_module.UUID = field(default_factory=uuid_module.uuid4)
    registro_foro_id: int | None = None
    estado: EstadoAlertaForo = EstadoAlertaForo.PENDIENTE

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise AlertaForoInvalidaError("AlertaForo requiere persona_master_id")
        if not self.descripcion or not self.descripcion.strip():
            raise AlertaForoInvalidaError("AlertaForo requiere descripcion no vacia")
        self.descripcion = self.descripcion.strip()

    def marcar_enviada(self) -> None:
        self.estado = EstadoAlertaForo.ENVIADA

    def descartar(self) -> None:
        self.estado = EstadoAlertaForo.DESCARTADA
