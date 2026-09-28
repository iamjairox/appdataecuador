"""Entidad de dominio: AlertaAcademica -- Submodulo 7.8 (Motor de Alertas)."""

from __future__ import annotations

import uuid as uuid_module
from dataclasses import dataclass, field
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import AlertaAcademicaInvalidaError
from govdata.domain.value_objects.estado_alerta_academica import EstadoAlertaAcademica
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_academica import TipoAlertaAcademica


@dataclass(slots=True)
class AlertaAcademica:
    persona_master_id: int
    tipo: TipoAlertaAcademica
    prioridad: NivelCriticidad
    descripcion: str
    detectado_en: datetime
    id: uuid_module.UUID = field(default_factory=uuid_module.uuid4)
    titulo_academico_id: int | None = None
    estado: EstadoAlertaAcademica = EstadoAlertaAcademica.PENDIENTE

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise AlertaAcademicaInvalidaError("AlertaAcademica requiere persona_master_id")
        if not self.descripcion or not self.descripcion.strip():
            raise AlertaAcademicaInvalidaError("AlertaAcademica requiere descripcion no vacia")
        self.descripcion = self.descripcion.strip()

    def marcar_enviada(self) -> None:
        self.estado = EstadoAlertaAcademica.ENVIADA

    def descartar(self) -> None:
        self.estado = EstadoAlertaAcademica.DESCARTADA
