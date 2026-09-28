"""Mapper: EventoForoModel <-> EventoForo (dominio)."""

from __future__ import annotations

from govdata.domain.entities.evento_foro import EventoForo
from govdata.infrastructure.persistence.postgresql.models.evento_foro_model import EventoForoModel


def a_dominio(modelo: EventoForoModel) -> EventoForo:
    return EventoForo(
        id=modelo.id, tipo=modelo.tipo, persona_master_id=modelo.persona_master_id, payload=modelo.payload,
        estado=modelo.estado, creado_en=modelo.creado_en, consumido_en=modelo.consumido_en,
        procesado_en=modelo.procesado_en,
    )


def a_modelo(evento: EventoForo, modelo: EventoForoModel | None = None) -> EventoForoModel:
    modelo = modelo or EventoForoModel()
    modelo.id = evento.id
    modelo.tipo = evento.tipo
    modelo.persona_master_id = evento.persona_master_id
    modelo.payload = evento.payload
    modelo.estado = evento.estado
    modelo.creado_en = evento.creado_en
    modelo.consumido_en = evento.consumido_en
    modelo.procesado_en = evento.procesado_en
    return modelo
