"""Mapper: TituloVersionAcademicaModel <-> TituloVersionAcademica (dominio)."""

from __future__ import annotations

from govdata.domain.entities.titulo_version_academica import TituloVersionAcademica
from govdata.infrastructure.persistence.postgresql.models.titulo_version_academica_model import (
    TituloVersionAcademicaModel,
)


def a_dominio(modelo: TituloVersionAcademicaModel) -> TituloVersionAcademica:
    return TituloVersionAcademica(
        id=modelo.id, persona_master_id=modelo.persona_master_id, clave_titulo=modelo.clave_titulo,
        numero_version=modelo.numero_version, titulo=modelo.titulo, nivel=modelo.nivel,
        institucion=modelo.institucion, fecha_inicio=modelo.fecha_inicio, fecha_registro=modelo.fecha_registro,
        pais=modelo.pais, estado=modelo.estado, modalidad=modelo.modalidad, numero_registro=modelo.numero_registro,
        area_conocimiento=modelo.area_conocimiento, tipo_titulo=modelo.tipo_titulo,
        fecha_graduacion=modelo.fecha_graduacion, observaciones=modelo.observaciones, fecha_fin=modelo.fecha_fin,
        estado_version=modelo.estado_version, consulta_senescyt_id=modelo.consulta_senescyt_id,
        creado_en=modelo.creado_en,
    )


def a_modelo(
    version: TituloVersionAcademica, modelo: TituloVersionAcademicaModel | None = None
) -> TituloVersionAcademicaModel:
    modelo = modelo or TituloVersionAcademicaModel()
    if version.id is not None:
        modelo.id = version.id
    modelo.persona_master_id = version.persona_master_id
    modelo.clave_titulo = version.clave_titulo
    modelo.numero_version = version.numero_version
    modelo.titulo = version.titulo
    modelo.nivel = version.nivel
    modelo.institucion = version.institucion
    modelo.fecha_inicio = version.fecha_inicio
    modelo.fecha_registro = version.fecha_registro
    modelo.pais = version.pais
    modelo.estado = version.estado
    modelo.modalidad = version.modalidad
    modelo.numero_registro = version.numero_registro
    modelo.area_conocimiento = version.area_conocimiento
    modelo.tipo_titulo = version.tipo_titulo
    modelo.fecha_graduacion = version.fecha_graduacion
    modelo.observaciones = version.observaciones
    modelo.fecha_fin = version.fecha_fin
    modelo.estado_version = version.estado_version
    modelo.consulta_senescyt_id = version.consulta_senescyt_id
    if version.creado_en is not None:
        modelo.creado_en = version.creado_en
    return modelo
