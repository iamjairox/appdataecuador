"""Mapper: AlertaPerfilModel <-> AlertaPerfil (dominio)."""

from __future__ import annotations

from govdata.domain.entities.alerta_perfil import AlertaPerfil
from govdata.infrastructure.persistence.postgresql.models.alerta_perfil_model import (
    AlertaPerfilModel,
)


def a_dominio(modelo: AlertaPerfilModel) -> AlertaPerfil:
    return AlertaPerfil(
        id=modelo.id,
        persona_master_id=modelo.persona_master_id,
        tipo=modelo.tipo,
        prioridad=modelo.prioridad,
        descripcion=modelo.descripcion,
        detectado_en=modelo.detectado_en,
        estado=modelo.estado,
        registro_fuente_id=modelo.registro_fuente_id,
    )


def a_modelo(alerta: AlertaPerfil, modelo: AlertaPerfilModel | None = None) -> AlertaPerfilModel:
    modelo = modelo or AlertaPerfilModel()
    modelo.id = alerta.id
    modelo.persona_master_id = alerta.persona_master_id
    modelo.tipo = alerta.tipo
    modelo.prioridad = alerta.prioridad
    modelo.descripcion = alerta.descripcion
    modelo.detectado_en = alerta.detectado_en
    modelo.estado = alerta.estado
    modelo.registro_fuente_id = alerta.registro_fuente_id
    return modelo
