"""Entidad de dominio: EventoAcademico -- Submodulo 7.9 (Motor de
Eventos). Mismo patron que `EventoPerfil` (Modulo 6): cola PENDIENTE ->
CONSUMIDO -> PROCESADO, preparacion para un futuro consumidor (n8n/
Dashboard/API, ninguno implementado en el Modulo 7)."""

from __future__ import annotations

import uuid as uuid_module
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from govdata.domain.exceptions.domain_exceptions import EventoAcademicoInvalidoError
from govdata.domain.value_objects.estado_evento_academico import EstadoEventoAcademico
from govdata.domain.value_objects.tipo_evento_academico import TipoEventoAcademico

_TRANSICIONES_VALIDAS: dict[EstadoEventoAcademico, set[EstadoEventoAcademico]] = {
    EstadoEventoAcademico.PENDIENTE: {EstadoEventoAcademico.CONSUMIDO},
    EstadoEventoAcademico.CONSUMIDO: {EstadoEventoAcademico.PROCESADO},
    EstadoEventoAcademico.PROCESADO: set(),
}


@dataclass(slots=True)
class EventoAcademico:
    tipo: TipoEventoAcademico
    persona_master_id: int
    payload: dict[str, Any]
    creado_en: datetime
    id: uuid_module.UUID = field(default_factory=uuid_module.uuid4)
    estado: EstadoEventoAcademico = EstadoEventoAcademico.PENDIENTE
    consumido_en: datetime | None = None
    procesado_en: datetime | None = None

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise EventoAcademicoInvalidoError("EventoAcademico requiere persona_master_id")

    def _transicionar(self, nuevo_estado: EstadoEventoAcademico, cuando: datetime) -> None:
        permitidos = _TRANSICIONES_VALIDAS.get(self.estado, set())
        if nuevo_estado not in permitidos:
            raise EventoAcademicoInvalidoError(f"Transicion invalida: {self.estado.value} -> {nuevo_estado.value}")
        self.estado = nuevo_estado

    def consumir(self, cuando: datetime) -> None:
        self._transicionar(EstadoEventoAcademico.CONSUMIDO, cuando)
        self.consumido_en = cuando

    def procesar(self, cuando: datetime) -> None:
        self._transicionar(EstadoEventoAcademico.PROCESADO, cuando)
        self.procesado_en = cuando
