"""Mapper: EventoPerfilModel <-> EventoPerfil (dominio)."""

from __future__ import annotations

from govdata.domain.entities.evento_perfil import EventoPerfil
from govdata.infrastructure.persistence.postgresql.models.evento_perfil_model import (
    EventoPerfilModel,
)


def a_dominio(modelo: EventoPerfilModel) -> EventoPerfil:
    return EventoPerfil(
        id=modelo.id,
        tipo=modelo.tipo,
        persona_master_id=modelo.persona_master_id,
        payload=modelo.payload,
        estado=modelo.estado,
        creado_en=modelo.creado_en,
        consumido_en=modelo.consumido_en,
        procesado_en=modelo.procesado_en,
    )


def a_modelo(evento: EventoPerfil, modelo: EventoPerfilModel | None = None) -> EventoPerfilModel:
    modelo = modelo or EventoPerfilModel()
    modelo.id = evento.id
    modelo.tipo = evento.tipo
    modelo.persona_master_id = evento.persona_master_id
    modelo.payload = evento.payload
    modelo.estado = evento.estado
    modelo.creado_en = evento.creado_en
    modelo.consumido_en = evento.consumido_en
    modelo.procesado_en = evento.procesado_en
    return modelo
