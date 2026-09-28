"""Servicio: EventoPerfilService -- Submodulo 6.12, mismo patron que
`EventoService` (Modulo 5): "solo generar eventos", ningun consumidor
(n8n/Dashboard/API) implementado todavia."""

from __future__ import annotations

import uuid
from datetime import datetime

from govdata.application.ports.evento_perfil_repository_port import EventoPerfilRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.evento_perfil import EventoPerfil
from govdata.domain.exceptions.domain_exceptions import EventoPerfilInvalidoError

logger = get_logger(__name__)


class EventoPerfilService:
    def __init__(self, evento_perfil_repository: EventoPerfilRepositoryPort) -> None:
        self._repository = evento_perfil_repository

    def guardar_lote(self, eventos: list[EventoPerfil]) -> list[EventoPerfil]:
        if not eventos:
            return []
        guardados = self._repository.guardar_lote(eventos)
        logger.info("eventos_perfil_creados", cantidad=len(guardados))
        return guardados

    def consumir(self, evento_id: uuid.UUID, cuando: datetime) -> EventoPerfil:
        evento = self._repository.buscar_por_id(evento_id)
        if evento is None:
            raise EventoPerfilInvalidoError(f"EventoPerfil no encontrado: {evento_id}")
        evento.consumir(cuando)
        return self._repository.guardar(evento)

    def procesar(self, evento_id: uuid.UUID, cuando: datetime) -> EventoPerfil:
        evento = self._repository.buscar_por_id(evento_id)
        if evento is None:
            raise EventoPerfilInvalidoError(f"EventoPerfil no encontrado: {evento_id}")
        evento.procesar(cuando)
        return self._repository.guardar(evento)

    def listar_pendientes(self, limite: int = 100) -> list[EventoPerfil]:
        return self._repository.listar_pendientes(limite)
