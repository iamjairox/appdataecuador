"""Mapper: ConsultaSenescytModel <-> ConsultaSenescyt (dominio)."""

from __future__ import annotations

from govdata.domain.entities.consulta_senescyt import ConsultaSenescyt
from govdata.infrastructure.persistence.postgresql.models.consulta_senescyt_model import (
    ConsultaSenescytModel,
)


def a_dominio(modelo: ConsultaSenescytModel) -> ConsultaSenescyt:
    return ConsultaSenescyt(
        id=modelo.id, persona_master_id=modelo.persona_master_id, iniciado_en=modelo.iniciado_en,
        finalizado_en=modelo.finalizado_en, exito=modelo.exito, duracion_segundos=modelo.duracion_segundos,
        error=modelo.error, reintentos=modelo.reintentos, cache_utilizado=modelo.cache_utilizado,
        version_resultante=modelo.version_resultante, respuesta_cruda=modelo.respuesta_cruda,
    )


def a_modelo(consulta: ConsultaSenescyt, modelo: ConsultaSenescytModel | None = None) -> ConsultaSenescytModel:
    modelo = modelo or ConsultaSenescytModel()
    if consulta.id is not None:
        modelo.id = consulta.id
    modelo.persona_master_id = consulta.persona_master_id
    modelo.iniciado_en = consulta.iniciado_en
    modelo.finalizado_en = consulta.finalizado_en
    modelo.exito = consulta.exito
    modelo.duracion_segundos = consulta.duracion_segundos
    modelo.error = consulta.error
    modelo.reintentos = consulta.reintentos
    modelo.cache_utilizado = consulta.cache_utilizado
    modelo.version_resultante = consulta.version_resultante
    modelo.respuesta_cruda = consulta.respuesta_cruda
    return modelo
