"""Mapper: HistorialAcademicoModel <-> HistorialAcademico (dominio)."""

from __future__ import annotations

from govdata.domain.entities.historial_academico import HistorialAcademico
from govdata.infrastructure.persistence.postgresql.models.historial_academico_model import (
    HistorialAcademicoModel,
)


def a_dominio(modelo: HistorialAcademicoModel) -> HistorialAcademico:
    return HistorialAcademico(
        id=modelo.id, persona_master_id=modelo.persona_master_id, clave_titulo=modelo.clave_titulo,
        tipo_cambio=modelo.tipo_cambio, detectado_en=modelo.detectado_en,
        consulta_senescyt_id=modelo.consulta_senescyt_id, ejecutado_por=modelo.ejecutado_por,
        titulo_academico_id=modelo.titulo_academico_id, campos_modificados=modelo.campos_modificados,
        descripcion=modelo.descripcion,
    )


def a_modelo(registro: HistorialAcademico, modelo: HistorialAcademicoModel | None = None) -> HistorialAcademicoModel:
    modelo = modelo or HistorialAcademicoModel()
    if registro.id is not None:
        modelo.id = registro.id
    modelo.persona_master_id = registro.persona_master_id
    modelo.clave_titulo = registro.clave_titulo
    modelo.tipo_cambio = registro.tipo_cambio
    modelo.detectado_en = registro.detectado_en
    modelo.consulta_senescyt_id = registro.consulta_senescyt_id
    modelo.ejecutado_por = registro.ejecutado_por
    modelo.titulo_academico_id = registro.titulo_academico_id
    modelo.campos_modificados = registro.campos_modificados
    modelo.descripcion = registro.descripcion
    return modelo
