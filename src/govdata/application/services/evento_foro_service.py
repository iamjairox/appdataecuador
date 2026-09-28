"""Servicio: EventoForoService -- Submodulo 8.7, mismo patron que
`EventoAcademicoService` (Modulo 7): "solo generar eventos", ningun
consumidor (n8n/Dashboard/API) implementado todavia."""

from __future__ import annotations

import uuid
from datetime import datetime

from govdata.application.ports.evento_foro_repository_port import EventoForoRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.evento_foro import EventoForo
from govdata.domain.exceptions.domain_exceptions import EventoForoInvalidoError

logger = get_logger(__name__)


class EventoForoService:
    def __init__(self, evento_repository: EventoForoRepositoryPort) -> None:
        self._repository = evento_repository

    def guardar_lote(self, eventos: list[EventoForo]) -> list[EventoForo]:
        if not eventos:
            return []
        guardados = self._repository.guardar_lote(eventos)
        logger.info("eventos_foro_creados", cantidad=len(guardados))
        return guardados

    def consumir(self, evento_id: uuid.UUID, cuando: datetime) -> EventoForo:
        evento = self._repository.buscar_por_id(evento_id)
        if evento is None:
            raise EventoForoInvalidoError(f"EventoForo no encontrado: {evento_id}")
        evento.consumir(cuando)
        return self._repository.guardar(evento)

    def procesar(self, evento_id: uuid.UUID, cuando: datetime) -> EventoForo:
        evento = self._repository.buscar_por_id(evento_id)
        if evento is None:
            raise EventoForoInvalidoError(f"EventoForo no encontrado: {evento_id}")
        evento.procesar(cuando)
        return self._repository.guardar(evento)

    def listar_pendientes(self, limite: int = 100) -> list[EventoForo]:
        return self._repository.listar_pendientes(limite)
