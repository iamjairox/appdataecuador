"""Entidad de dominio: Evento -- Submodulo 5.7 (Notificaciones, preparacion).

"NO enviar correos todavia. NO integrar WhatsApp. NO integrar n8n. Solo
generar eventos" -- instruccion explicita del cliente. `Evento` es la cola
que un futuro consumidor externo (n8n, Dashboard, API) leera y avanzara:

    PENDIENTE -> CONSUMIDO -> PROCESADO

Este modulo NUNCA transiciona un evento mas alla de crearlo en PENDIENTE;
`consumir()`/`procesar()` existen para que ese futuro consumidor los
invoque via la capa que se construya despues (API/worker de notificaciones),
no para que el Modulo 5 los use internamente.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from govdata.domain.exceptions.domain_exceptions import EventoInvalidoError


class TipoEvento(str, Enum):
    ALERTA = "alerta"
    OPORTUNIDAD_COMERCIAL = "oportunidad_comercial"


class EstadoEvento(str, Enum):
    PENDIENTE = "pendiente"
    CONSUMIDO = "consumido"
    PROCESADO = "procesado"


_TRANSICIONES_VALIDAS: dict[EstadoEvento, frozenset[EstadoEvento]] = {
    EstadoEvento.PENDIENTE: frozenset({EstadoEvento.CONSUMIDO}),
    EstadoEvento.CONSUMIDO: frozenset({EstadoEvento.PROCESADO}),
    EstadoEvento.PROCESADO: frozenset(),
}


@dataclass(slots=True)
class Evento:
    """Un evento estructurado en cola, pendiente de ser leido por un
    consumidor externo (n8n/Dashboard/API -- fuera de alcance del Modulo 5)."""

    tipo: TipoEvento
    entidad_id: int
    referencia_id: uuid.UUID
    """id de la Alerta u OportunidadComercial que origino este evento."""
    payload: dict
    creado_en: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    estado: EstadoEvento = EstadoEvento.PENDIENTE
    consumido_en: datetime | None = None
    procesado_en: datetime | None = None

    def _transicionar(self, nuevo_estado: EstadoEvento) -> None:
        permitidos = _TRANSICIONES_VALIDAS[self.estado]
        if nuevo_estado not in permitidos:
            raise EventoInvalidoError(
                f"Transicion invalida: {self.estado.value} -> {nuevo_estado.value} (evento_id={self.id})"
            )
        self.estado = nuevo_estado

    def consumir(self, cuando: datetime) -> None:
        self._transicionar(EstadoEvento.CONSUMIDO)
        self.consumido_en = cuando

    def procesar(self, cuando: datetime) -> None:
        self._transicionar(EstadoEvento.PROCESADO)
        self.procesado_en = cuando
