"""Mapper: EventoAcademicoModel <-> EventoAcademico (dominio)."""

from __future__ import annotations

from govdata.domain.entities.evento_academico import EventoAcademico
from govdata.infrastructure.persistence.postgresql.models.evento_academico_model import (
    EventoAcademicoModel,
)


def a_dominio(modelo: EventoAcademicoModel) -> EventoAcademico:
    return EventoAcademico(
        id=modelo.id, tipo=modelo.tipo, persona_master_id=modelo.persona_master_id, payload=modelo.payload,
        estado=modelo.estado, creado_en=modelo.creado_en, consumido_en=modelo.consumido_en,
        procesado_en=modelo.procesado_en,
    )


def a_modelo(evento: EventoAcademico, modelo: EventoAcademicoModel | None = None) -> EventoAcademicoModel:
    modelo = modelo or EventoAcademicoModel()
    modelo.id = evento.id
    modelo.tipo = evento.tipo
    modelo.persona_master_id = evento.persona_master_id
    modelo.payload = evento.payload
    modelo.estado = evento.estado
    modelo.creado_en = evento.creado_en
    modelo.consumido_en = evento.consumido_en
    modelo.procesado_en = evento.procesado_en
    return modelo
