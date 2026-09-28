"""Entidad de dominio: AlertaPerfil -- Submodulo 6.13 (Alertas)."""

from __future__ import annotations

import uuid as uuid_module
from dataclasses import dataclass, field
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import AlertaPerfilInvalidaError
from govdata.domain.value_objects.estado_alerta_perfil import EstadoAlertaPerfil
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_perfil import TipoAlertaPerfil


@dataclass(slots=True)
class AlertaPerfil:
    """Alerta generada por un cambio relevante en el perfil de una Persona."""

    persona_master_id: int
    tipo: TipoAlertaPerfil
    prioridad: NivelCriticidad
    descripcion: str
    detectado_en: datetime
    id: uuid_module.UUID = field(default_factory=uuid_module.uuid4)
    registro_fuente_id: int | None = None
    estado: EstadoAlertaPerfil = EstadoAlertaPerfil.PENDIENTE

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise AlertaPerfilInvalidaError("AlertaPerfil requiere persona_master_id")
        if not self.descripcion or not self.descripcion.strip():
            raise AlertaPerfilInvalidaError("AlertaPerfil requiere descripcion no vacia")
        self.descripcion = self.descripcion.strip()

    def marcar_enviada(self) -> None:
        self.estado = EstadoAlertaPerfil.ENVIADA

    def descartar(self) -> None:
        self.estado = EstadoAlertaPerfil.DESCARTADA
