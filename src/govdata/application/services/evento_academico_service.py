"""Servicio: EventoAcademicoService -- Submodulo 7.9, mismo patron que
`EventoPerfilService` (Modulo 6): "solo generar eventos", ningun
consumidor (n8n/Dashboard/API) implementado todavia."""

from __future__ import annotations

import uuid
from datetime import datetime

from govdata.application.ports.evento_academico_repository_port import (
    EventoAcademicoRepositoryPort,
)
from govdata.config.logging_config import get_logger
from govdata.domain.entities.evento_academico import EventoAcademico
from govdata.domain.exceptions.domain_exceptions import EventoAcademicoInvalidoError

logger = get_logger(__name__)


class EventoAcademicoService:
    def __init__(self, evento_repository: EventoAcademicoRepositoryPort) -> None:
        self._repository = evento_repository

    def guardar_lote(self, eventos: list[EventoAcademico]) -> list[EventoAcademico]:
        if not eventos:
            return []
        guardados = self._repository.guardar_lote(eventos)
        logger.info("eventos_academicos_creados", cantidad=len(guardados))
        return guardados

    def consumir(self, evento_id: uuid.UUID, cuando: datetime) -> EventoAcademico:
        evento = self._repository.buscar_por_id(evento_id)
        if evento is None:
            raise EventoAcademicoInvalidoError(f"EventoAcademico no encontrado: {evento_id}")
        evento.consumir(cuando)
        return self._repository.guardar(evento)

    def procesar(self, evento_id: uuid.UUID, cuando: datetime) -> EventoAcademico:
        evento = self._repository.buscar_por_id(evento_id)
        if evento is None:
            raise EventoAcademicoInvalidoError(f"EventoAcademico no encontrado: {evento_id}")
        evento.procesar(cuando)
        return self._repository.guardar(evento)

    def listar_pendientes(self, limite: int = 100) -> list[EventoAcademico]:
        return self._repository.listar_pendientes(limite)
