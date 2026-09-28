"""Mapper: EjecucionModel <-> Ejecucion (dominio)."""

from __future__ import annotations

from govdata.domain.entities.ejecucion import Ejecucion, EstadoEjecucion
from govdata.infrastructure.persistence.postgresql.models.ejecucion_model import EjecucionModel


def a_dominio(modelo: EjecucionModel) -> Ejecucion:
    return Ejecucion(
        id=modelo.id,
        entidad_id=modelo.entidad_id,
        etapa=modelo.etapa,
        estado=EstadoEjecucion(modelo.estado),
        mensaje_error=modelo.mensaje_error,
        intentos=modelo.intentos,
        iniciado_en=modelo.iniciado_en,
        finalizado_en=modelo.finalizado_en,
    )


def a_modelo(ejecucion: Ejecucion, modelo: EjecucionModel | None = None) -> EjecucionModel:
    modelo = modelo or EjecucionModel()
    if ejecucion.id is not None:
        modelo.id = ejecucion.id
    modelo.entidad_id = ejecucion.entidad_id
    modelo.etapa = ejecucion.etapa
    modelo.estado = ejecucion.estado.value
    modelo.mensaje_error = ejecucion.mensaje_error
    modelo.intentos = ejecucion.intentos
    modelo.iniciado_en = ejecucion.iniciado_en
    modelo.finalizado_en = ejecucion.finalizado_en
    return modelo
