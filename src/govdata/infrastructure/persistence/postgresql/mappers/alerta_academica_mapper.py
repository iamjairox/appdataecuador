"""Mapper: AlertaAcademicaModel <-> AlertaAcademica (dominio)."""

from __future__ import annotations

from govdata.domain.entities.alerta_academica import AlertaAcademica
from govdata.infrastructure.persistence.postgresql.models.alerta_academica_model import (
    AlertaAcademicaModel,
)


def a_dominio(modelo: AlertaAcademicaModel) -> AlertaAcademica:
    return AlertaAcademica(
        id=modelo.id, persona_master_id=modelo.persona_master_id, tipo=modelo.tipo, prioridad=modelo.prioridad,
        descripcion=modelo.descripcion, detectado_en=modelo.detectado_en, estado=modelo.estado,
        titulo_academico_id=modelo.titulo_academico_id,
    )


def a_modelo(alerta: AlertaAcademica, modelo: AlertaAcademicaModel | None = None) -> AlertaAcademicaModel:
    modelo = modelo or AlertaAcademicaModel()
    modelo.id = alerta.id
    modelo.persona_master_id = alerta.persona_master_id
    modelo.tipo = alerta.tipo
    modelo.prioridad = alerta.prioridad
    modelo.descripcion = alerta.descripcion
    modelo.detectado_en = alerta.detectado_en
    modelo.estado = alerta.estado
    modelo.titulo_academico_id = alerta.titulo_academico_id
    return modelo
