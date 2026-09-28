"""Entidad de dominio: EventoForo -- Submodulo 8.7 (Motor de Eventos).
Mismo patron que `EventoAcademico` (Modulo 7): cola PENDIENTE ->
CONSUMIDO -> PROCESADO, preparacion para un futuro consumidor (n8n/
Dashboard/API, ninguno implementado en el Modulo 8)."""

from __future__ import annotations

import uuid as uuid_module
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from govdata.domain.exceptions.domain_exceptions import EventoForoInvalidoError
from govdata.domain.value_objects.estado_evento_foro import EstadoEventoForo
from govdata.domain.value_objects.tipo_evento_foro import TipoEventoForo

_TRANSICIONES_VALIDAS: dict[EstadoEventoForo, set[EstadoEventoForo]] = {
    EstadoEventoForo.PENDIENTE: {EstadoEventoForo.CONSUMIDO},
    EstadoEventoForo.CONSUMIDO: {EstadoEventoForo.PROCESADO},
    EstadoEventoForo.PROCESADO: set(),
}


@dataclass(slots=True)
class EventoForo:
    tipo: TipoEventoForo
    persona_master_id: int
    payload: dict[str, Any]
    creado_en: datetime
    id: uuid_module.UUID = field(default_factory=uuid_module.uuid4)
    estado: EstadoEventoForo = EstadoEventoForo.PENDIENTE
    consumido_en: datetime | None = None
    procesado_en: datetime | None = None

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise EventoForoInvalidoError("EventoForo requiere persona_master_id")

    def _transicionar(self, nuevo_estado: EstadoEventoForo, cuando: datetime) -> None:
        permitidos = _TRANSICIONES_VALIDAS.get(self.estado, set())
        if nuevo_estado not in permitidos:
            raise EventoForoInvalidoError(f"Transicion invalida: {self.estado.value} -> {nuevo_estado.value}")
        self.estado = nuevo_estado

    def consumir(self, cuando: datetime) -> None:
        self._transicionar(EstadoEventoForo.CONSUMIDO, cuando)
        self.consumido_en = cuando

    def procesar(self, cuando: datetime) -> None:
        self._transicionar(EstadoEventoForo.PROCESADO, cuando)
        self.procesado_en = cuando
