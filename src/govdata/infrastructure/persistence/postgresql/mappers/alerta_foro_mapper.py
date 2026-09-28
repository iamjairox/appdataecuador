"""Mapper: AlertaForoModel <-> AlertaForo (dominio)."""

from __future__ import annotations

from govdata.domain.entities.alerta_foro import AlertaForo
from govdata.infrastructure.persistence.postgresql.models.alerta_foro_model import AlertaForoModel


def a_dominio(modelo: AlertaForoModel) -> AlertaForo:
    return AlertaForo(
        id=modelo.id, persona_master_id=modelo.persona_master_id, tipo=modelo.tipo, prioridad=modelo.prioridad,
        descripcion=modelo.descripcion, detectado_en=modelo.detectado_en, estado=modelo.estado,
        registro_foro_id=modelo.registro_foro_id,
    )


def a_modelo(alerta: AlertaForo, modelo: AlertaForoModel | None = None) -> AlertaForoModel:
    modelo = modelo or AlertaForoModel()
    modelo.id = alerta.id
    modelo.persona_master_id = alerta.persona_master_id
    modelo.tipo = alerta.tipo
    modelo.prioridad = alerta.prioridad
    modelo.descripcion = alerta.descripcion
    modelo.detectado_en = alerta.detectado_en
    modelo.estado = alerta.estado
    modelo.registro_foro_id = alerta.registro_foro_id
    return modelo
