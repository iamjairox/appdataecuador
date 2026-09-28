"""Entidad de dominio: EventoPerfil -- Submodulo 6.12 (Eventos) + 6.7
(preparacion de notificaciones, mismo patron que `Evento` de Modulo 5:
"solo generar eventos", ningun consumidor -- n8n/Dashboard/API -- se
implementa todavia)."""

from __future__ import annotations

import uuid as uuid_module
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from govdata.domain.exceptions.domain_exceptions import EventoPerfilInvalidoError
from govdata.domain.value_objects.estado_evento_perfil import EstadoEventoPerfil
from govdata.domain.value_objects.tipo_evento_identidad import TipoEventoIdentidad

_TRANSICIONES_VALIDAS: dict[EstadoEventoPerfil, set[EstadoEventoPerfil]] = {
    EstadoEventoPerfil.PENDIENTE: {EstadoEventoPerfil.CONSUMIDO},
    EstadoEventoPerfil.CONSUMIDO: {EstadoEventoPerfil.PROCESADO},
    EstadoEventoPerfil.PROCESADO: set(),
}


@dataclass(slots=True)
class EventoPerfil:
    """Evento de dominio sobre el perfil consolidado de una Persona."""

    tipo: TipoEventoIdentidad
    persona_master_id: int
    payload: dict[str, Any]
    creado_en: datetime
    id: uuid_module.UUID = field(default_factory=uuid_module.uuid4)
    estado: EstadoEventoPerfil = EstadoEventoPerfil.PENDIENTE
    consumido_en: datetime | None = None
    procesado_en: datetime | None = None

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise EventoPerfilInvalidoError("EventoPerfil requiere persona_master_id")

    def _transicionar(self, nuevo_estado: EstadoEventoPerfil, cuando: datetime) -> None:
        permitidos = _TRANSICIONES_VALIDAS.get(self.estado, set())
        if nuevo_estado not in permitidos:
            raise EventoPerfilInvalidoError(
                f"Transicion invalida: {self.estado.value} -> {nuevo_estado.value}"
            )
        self.estado = nuevo_estado

    def consumir(self, cuando: datetime) -> None:
        self._transicionar(EstadoEventoPerfil.CONSUMIDO, cuando)
        self.consumido_en = cuando

    def procesar(self, cuando: datetime) -> None:
        self._transicionar(EstadoEventoPerfil.PROCESADO, cuando)
        self.procesado_en = cuando
