"""Mapper: HistorialForoModel <-> HistorialForo (dominio)."""

from __future__ import annotations

from govdata.domain.entities.historial_foro import HistorialForo
from govdata.infrastructure.persistence.postgresql.models.historial_foro_model import (
    HistorialForoModel,
)


def a_dominio(modelo: HistorialForoModel) -> HistorialForo:
    return HistorialForo(
        id=modelo.id, persona_master_id=modelo.persona_master_id, clave_registro=modelo.clave_registro,
        tipo_cambio=modelo.tipo_cambio, detectado_en=modelo.detectado_en, consulta_foro_id=modelo.consulta_foro_id,
        ejecutado_por=modelo.ejecutado_por, registro_foro_id=modelo.registro_foro_id,
        campos_modificados=modelo.campos_modificados, descripcion=modelo.descripcion,
    )


def a_modelo(historial: HistorialForo, modelo: HistorialForoModel | None = None) -> HistorialForoModel:
    modelo = modelo or HistorialForoModel()
    if historial.id is not None:
        modelo.id = historial.id
    modelo.persona_master_id = historial.persona_master_id
    modelo.clave_registro = historial.clave_registro
    modelo.tipo_cambio = historial.tipo_cambio
    modelo.detectado_en = historial.detectado_en
    modelo.consulta_foro_id = historial.consulta_foro_id
    modelo.ejecutado_por = historial.ejecutado_por
    modelo.registro_foro_id = historial.registro_foro_id
    modelo.campos_modificados = historial.campos_modificados
    modelo.descripcion = historial.descripcion
    return modelo
