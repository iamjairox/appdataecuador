"""Mapper: EventoModel <-> Evento (dominio)."""

from __future__ import annotations

from govdata.domain.entities.evento import Evento
from govdata.infrastructure.persistence.postgresql.models.evento_model import EventoModel


def a_dominio(modelo: EventoModel) -> Evento:
    return Evento(
        id=modelo.id,
        tipo=modelo.tipo,
        entidad_id=modelo.entidad_id,
        referencia_id=modelo.referencia_id,
        payload=dict(modelo.payload or {}),
        creado_en=modelo.creado_en,
        estado=modelo.estado,
        consumido_en=modelo.consumido_en,
        procesado_en=modelo.procesado_en,
    )


def a_modelo(evento: Evento, modelo: EventoModel | None = None) -> EventoModel:
    modelo = modelo or EventoModel()
    modelo.id = evento.id
    modelo.tipo = evento.tipo
    modelo.entidad_id = evento.entidad_id
    modelo.referencia_id = evento.referencia_id
    modelo.payload = dict(evento.payload)
    modelo.creado_en = evento.creado_en
    modelo.estado = evento.estado
    modelo.consumido_en = evento.consumido_en
    modelo.procesado_en = evento.procesado_en
    return modelo
