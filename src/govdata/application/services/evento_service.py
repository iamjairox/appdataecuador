"""Servicio: EventoService -- Submodulo 5.7 (Notificaciones, preparacion).

"NO enviar correos todavia. NO integrar WhatsApp. NO integrar n8n. Solo
generar eventos" -- este servicio crea `Evento` en PENDIENTE a partir de
`Alerta`/`OportunidadComercial` ya persistidas, y expone `consumir()`/
`procesar()` para que un FUTURO consumidor externo los invoque -- el
Modulo 5 nunca los llama a si mismo."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime

from govdata.application.dto.alerta_dto import AlertaDTO
from govdata.application.dto.oportunidad_comercial_dto import OportunidadComercialDTO
from govdata.application.ports.evento_repository_port import EventoRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.alerta import Alerta
from govdata.domain.entities.evento import Evento, TipoEvento
from govdata.domain.entities.oportunidad_comercial import OportunidadComercial
from govdata.domain.exceptions.domain_exceptions import EventoInvalidoError

logger = get_logger(__name__)


def _payload(dto: AlertaDTO | OportunidadComercialDTO) -> dict:
    """`Evento.payload` se persiste en una columna JSON real -- las fechas
    del DTO original (ej. `detectado_en: datetime`) deben quedar como
    texto ANTES de llegar al driver de base de datos, o el serializador
    JSON del motor (que no sabe de `datetime`) falla al insertar."""

    def _serializar(valor: object) -> str:
        if hasattr(valor, "isoformat"):
            return valor.isoformat()
        raise TypeError(f"No se puede serializar en el payload del evento: {type(valor)}")

    return json.loads(json.dumps(asdict(dto), default=_serializar))


class EventoService:
    def __init__(self, evento_repository: EventoRepositoryPort) -> None:
        self._evento_repository = evento_repository

    def crear_desde_alertas(self, alertas: list[Alerta], creado_en: datetime) -> list[Evento]:
        eventos = [
            Evento(
                tipo=TipoEvento.ALERTA,
                entidad_id=alerta.entidad_id,
                referencia_id=alerta.id,
                payload=_payload(AlertaDTO.desde_entidad(alerta)),
                creado_en=creado_en,
            )
            for alerta in alertas
        ]
        return self._guardar_lote(eventos)

    def crear_desde_oportunidades(self, oportunidades: list[OportunidadComercial], creado_en: datetime) -> list[Evento]:
        eventos = [
            Evento(
                tipo=TipoEvento.OPORTUNIDAD_COMERCIAL,
                entidad_id=oportunidad.entidad_id,
                referencia_id=oportunidad.id,
                payload=_payload(OportunidadComercialDTO.desde_entidad(oportunidad)),
                creado_en=creado_en,
            )
            for oportunidad in oportunidades
        ]
        return self._guardar_lote(eventos)

    def _guardar_lote(self, eventos: list[Evento]) -> list[Evento]:
        if not eventos:
            return []
        guardados = self._evento_repository.guardar_lote(eventos)
        logger.info("eventos_creados", cantidad=len(guardados))
        return guardados

    def consumir(self, evento_id: uuid.UUID, cuando: datetime) -> Evento:
        evento = self._evento_repository.buscar_por_id(evento_id)
        if evento is None:
            raise EventoInvalidoError(f"Evento no encontrado: {evento_id}")
        evento.consumir(cuando)
        return self._evento_repository.guardar(evento)

    def procesar(self, evento_id: uuid.UUID, cuando: datetime) -> Evento:
        evento = self._evento_repository.buscar_por_id(evento_id)
        if evento is None:
            raise EventoInvalidoError(f"Evento no encontrado: {evento_id}")
        evento.procesar(cuando)
        return self._evento_repository.guardar(evento)

    def listar_pendientes(self, limite: int = 100) -> list[Evento]:
        return self._evento_repository.listar_pendientes(limite)
