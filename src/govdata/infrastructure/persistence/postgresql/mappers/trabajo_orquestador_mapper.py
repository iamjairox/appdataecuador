"""Mapper: TrabajoOrquestadorModel <-> TrabajoOrquestador (dominio)."""

from __future__ import annotations

from govdata.domain.entities.trabajo_orquestador import TrabajoOrquestador
from govdata.infrastructure.persistence.postgresql.models.trabajo_orquestador_model import (
    TrabajoOrquestadorModel,
)


def a_dominio(modelo: TrabajoOrquestadorModel) -> TrabajoOrquestador:
    return TrabajoOrquestador(
        id=modelo.id, tipo=modelo.tipo, parametros=dict(modelo.parametros), politica=modelo.politica,
        estado=modelo.estado, prioridad=modelo.prioridad, version_lock=modelo.version_lock,
        intentos=modelo.intentos, max_intentos=modelo.max_intentos, entidad_id=modelo.entidad_id,
        creado_en=modelo.creado_en, actualizado_en=modelo.actualizado_en, iniciado_en=modelo.iniciado_en,
        finalizado_en=modelo.finalizado_en, ultimo_error=modelo.ultimo_error,
    )


def a_modelo(trabajo: TrabajoOrquestador, modelo: TrabajoOrquestadorModel | None = None) -> TrabajoOrquestadorModel:
    modelo = modelo or TrabajoOrquestadorModel()
    modelo.id = trabajo.id
    modelo.tipo = trabajo.tipo
    modelo.parametros = trabajo.parametros
    modelo.politica = trabajo.politica
    modelo.estado = trabajo.estado
    modelo.prioridad = trabajo.prioridad
    modelo.version_lock = trabajo.version_lock
    modelo.intentos = trabajo.intentos
    modelo.max_intentos = trabajo.max_intentos
    modelo.entidad_id = trabajo.entidad_id
    modelo.actualizado_en = trabajo.actualizado_en
    modelo.iniciado_en = trabajo.iniciado_en
    modelo.finalizado_en = trabajo.finalizado_en
    modelo.ultimo_error = trabajo.ultimo_error
    if trabajo.creado_en is not None:
        modelo.creado_en = trabajo.creado_en
    return modelo
