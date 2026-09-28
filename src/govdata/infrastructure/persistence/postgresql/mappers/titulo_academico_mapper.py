"""Mapper: TituloAcademicoModel <-> TituloAcademico (dominio)."""

from __future__ import annotations

from govdata.domain.entities.titulo_academico import TituloAcademico
from govdata.infrastructure.persistence.postgresql.models.titulo_academico_model import (
    TituloAcademicoModel,
)


def a_dominio(modelo: TituloAcademicoModel) -> TituloAcademico:
    return TituloAcademico(
        id=modelo.id, persona_master_id=modelo.persona_master_id, clave_titulo=modelo.clave_titulo,
        titulo=modelo.titulo, nivel=modelo.nivel, institucion=modelo.institucion,
        fecha_registro=modelo.fecha_registro, pais=modelo.pais, estado=modelo.estado, modalidad=modelo.modalidad,
        numero_registro=modelo.numero_registro, area_conocimiento=modelo.area_conocimiento,
        tipo_titulo=modelo.tipo_titulo, fecha_graduacion=modelo.fecha_graduacion, observaciones=modelo.observaciones,
        numero_version=modelo.numero_version, vigente=modelo.vigente, fuente=modelo.fuente,
        fecha_consulta=modelo.fecha_consulta, nivel_confianza=modelo.nivel_confianza,
        version_fuente=modelo.version_fuente, evidencia=modelo.evidencia, creado_en=modelo.creado_en,
        actualizado_en=modelo.actualizado_en,
    )


def a_modelo(titulo: TituloAcademico, modelo: TituloAcademicoModel | None = None) -> TituloAcademicoModel:
    modelo = modelo or TituloAcademicoModel()
    if titulo.id is not None:
        modelo.id = titulo.id
    modelo.persona_master_id = titulo.persona_master_id
    modelo.clave_titulo = titulo.clave_titulo
    modelo.titulo = titulo.titulo
    modelo.nivel = titulo.nivel
    modelo.institucion = titulo.institucion
    modelo.fecha_registro = titulo.fecha_registro
    modelo.pais = titulo.pais
    modelo.estado = titulo.estado
    modelo.modalidad = titulo.modalidad
    modelo.numero_registro = titulo.numero_registro
    modelo.area_conocimiento = titulo.area_conocimiento
    modelo.tipo_titulo = titulo.tipo_titulo
    modelo.fecha_graduacion = titulo.fecha_graduacion
    modelo.observaciones = titulo.observaciones
    modelo.numero_version = titulo.numero_version
    modelo.vigente = titulo.vigente
    modelo.fuente = titulo.fuente
    modelo.fecha_consulta = titulo.fecha_consulta
    modelo.nivel_confianza = titulo.nivel_confianza
    modelo.version_fuente = titulo.version_fuente
    modelo.evidencia = titulo.evidencia
    if titulo.creado_en is not None:
        modelo.creado_en = titulo.creado_en
    if titulo.actualizado_en is not None:
        modelo.actualizado_en = titulo.actualizado_en
    return modelo
