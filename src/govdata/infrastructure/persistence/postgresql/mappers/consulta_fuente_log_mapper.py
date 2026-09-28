"""Mapper: ConsultaFuenteLogModel <-> ConsultaFuenteLog (dominio)."""

from __future__ import annotations

from govdata.domain.entities.consulta_fuente_log import ConsultaFuenteLog
from govdata.infrastructure.persistence.postgresql.models.consulta_fuente_log_model import (
    ConsultaFuenteLogModel,
)


def a_dominio(modelo: ConsultaFuenteLogModel) -> ConsultaFuenteLog:
    return ConsultaFuenteLog(
        id=modelo.id,
        persona_master_id=modelo.persona_master_id,
        fuente=modelo.fuente,
        iniciado_en=modelo.iniciado_en,
        finalizado_en=modelo.finalizado_en,
        exito=modelo.exito,
        duracion_segundos=modelo.duracion_segundos,
        reintentos=modelo.reintentos,
        error=modelo.error,
    )


def a_modelo(log: ConsultaFuenteLog, modelo: ConsultaFuenteLogModel | None = None) -> ConsultaFuenteLogModel:
    modelo = modelo or ConsultaFuenteLogModel()
    if log.id is not None:
        modelo.id = log.id
    modelo.persona_master_id = log.persona_master_id
    modelo.fuente = log.fuente
    modelo.iniciado_en = log.iniciado_en
    modelo.finalizado_en = log.finalizado_en
    modelo.exito = log.exito
    modelo.duracion_segundos = log.duracion_segundos
    modelo.reintentos = log.reintentos
    modelo.error = log.error
    return modelo
