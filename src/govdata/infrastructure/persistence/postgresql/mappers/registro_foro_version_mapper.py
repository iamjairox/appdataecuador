"""Mapper: RegistroForoVersionModel <-> RegistroForoVersion (dominio)."""

from __future__ import annotations

from govdata.domain.entities.registro_foro_version import RegistroForoVersion
from govdata.infrastructure.persistence.postgresql.models.registro_foro_version_model import (
    RegistroForoVersionModel,
)


def a_dominio(modelo: RegistroForoVersionModel) -> RegistroForoVersion:
    return RegistroForoVersion(
        id=modelo.id, persona_master_id=modelo.persona_master_id, clave_registro=modelo.clave_registro,
        numero_version=modelo.numero_version, nombre_completo=modelo.nombre_completo, registro=modelo.registro,
        provincia=modelo.provincia, estado=modelo.estado, cedula=modelo.cedula, fecha_inicio=modelo.fecha_inicio,
        fecha_fin=modelo.fecha_fin, estado_version=modelo.estado_version, consulta_foro_id=modelo.consulta_foro_id,
        creado_en=modelo.creado_en,
    )


def a_modelo(
    version: RegistroForoVersion, modelo: RegistroForoVersionModel | None = None
) -> RegistroForoVersionModel:
    modelo = modelo or RegistroForoVersionModel()
    if version.id is not None:
        modelo.id = version.id
    modelo.persona_master_id = version.persona_master_id
    modelo.clave_registro = version.clave_registro
    modelo.numero_version = version.numero_version
    modelo.nombre_completo = version.nombre_completo
    modelo.registro = version.registro
    modelo.provincia = version.provincia
    modelo.estado = version.estado
    modelo.cedula = version.cedula
    modelo.fecha_inicio = version.fecha_inicio
    modelo.fecha_fin = version.fecha_fin
    modelo.estado_version = version.estado_version
    modelo.consulta_foro_id = version.consulta_foro_id
    if version.creado_en is not None:
        modelo.creado_en = version.creado_en
    return modelo
