"""Mapper: AlertaModel <-> Alerta (dominio)."""

from __future__ import annotations

from govdata.domain.entities.alerta import Alerta
from govdata.infrastructure.persistence.postgresql.models.alerta_model import AlertaModel


def a_dominio(modelo: AlertaModel) -> Alerta:
    return Alerta(
        id=modelo.id,
        entidad_id=modelo.entidad_id,
        persona_id=modelo.persona_id,
        documento_id=modelo.documento_id,
        tipo=modelo.tipo,
        prioridad=modelo.prioridad,
        descripcion=modelo.descripcion,
        detectado_en=modelo.detectado_en,
        estado=modelo.estado,
    )


def a_modelo(alerta: Alerta, modelo: AlertaModel | None = None) -> AlertaModel:
    modelo = modelo or AlertaModel()
    modelo.id = alerta.id
    modelo.entidad_id = alerta.entidad_id
    modelo.persona_id = alerta.persona_id
    modelo.documento_id = alerta.documento_id
    modelo.tipo = alerta.tipo
    modelo.prioridad = alerta.prioridad
    modelo.descripcion = alerta.descripcion
    modelo.detectado_en = alerta.detectado_en
    modelo.estado = alerta.estado
    return modelo
