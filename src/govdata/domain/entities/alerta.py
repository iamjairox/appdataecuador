"""Entidad de dominio: Alerta -- Submodulo 5.6 (Alertas Inteligentes).

Se genera cuando el Motor de Comparacion (5.1) detecta un cambio que
`clasificador_criticidad` (Modulo 5, Rule Engine) considera relevante
para el negocio -- nunca por cada diferencia trivial. Cada `Alerta` es
inmutable en su contenido (que cambio, cuando, por que) salvo por su
`estado`, que solo avanza en un sentido: PENDIENTE -> ENVIADA|DESCARTADA.

NO envia nada por si misma (correo/WhatsApp/n8n quedan fuera del alcance
del Modulo 5, ver Submodulo 5.7): esta entidad es solo el registro
estructurado que un futuro consumidor (API, Dashboard, n8n) leera.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from govdata.domain.exceptions.domain_exceptions import AlertaInvalidaError
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad


class TipoAlerta(str, Enum):
    NUEVO_DIRECTOR_JURIDICO = "nuevo_director_juridico"
    NUEVO_DIRECTOR_FINANCIERO = "nuevo_director_financiero"
    NUEVO_PROCURADOR = "nuevo_procurador"
    NUEVO_ABOGADO = "nuevo_abogado"
    FUNCIONARIO_ELIMINADO = "funcionario_eliminado"
    CAMBIO_CORREO = "cambio_correo"
    CAMBIO_DEPENDENCIA = "cambio_dependencia"
    CAMBIO_CARGO = "cambio_cargo"
    CAMBIO_MASIVO = "cambio_masivo"
    CAMBIO_SUPERIOR_30_PORCIENTO = "cambio_superior_30_porciento"
    DOCUMENTO_VACIO = "documento_vacio"
    DOCUMENTO_SOSPECHOSO = "documento_sospechoso"


class EstadoAlerta(str, Enum):
    PENDIENTE = "pendiente"
    ENVIADA = "enviada"
    DESCARTADA = "descartada"


@dataclass(slots=True)
class Alerta:
    """Evento de negocio estructurado ante un cambio relevante."""

    entidad_id: int
    tipo: TipoAlerta
    prioridad: NivelCriticidad
    descripcion: str
    detectado_en: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    persona_id: int | None = None
    documento_id: int | None = None
    estado: EstadoAlerta = EstadoAlerta.PENDIENTE

    def __post_init__(self) -> None:
        if not self.descripcion or not self.descripcion.strip():
            raise AlertaInvalidaError(f"Alerta (tipo={self.tipo.value}) requiere descripcion no vacia")
        self.descripcion = self.descripcion.strip()

    def marcar_enviada(self) -> None:
        if self.estado != EstadoAlerta.PENDIENTE:
            raise AlertaInvalidaError(f"Solo una alerta PENDIENTE puede marcarse ENVIADA (actual: {self.estado.value})")
        self.estado = EstadoAlerta.ENVIADA

    def descartar(self) -> None:
        if self.estado != EstadoAlerta.PENDIENTE:
            raise AlertaInvalidaError(f"Solo una alerta PENDIENTE puede descartarse (actual: {self.estado.value})")
        self.estado = EstadoAlerta.DESCARTADA
