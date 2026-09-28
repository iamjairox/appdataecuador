"""Mapper: VersionFuncionarioModel <-> VersionFuncionario (dominio)."""

from __future__ import annotations

from govdata.domain.entities.version_funcionario import VersionFuncionario
from govdata.infrastructure.persistence.postgresql.models.version_funcionario_model import (
    VersionFuncionarioModel,
)


def a_dominio(modelo: VersionFuncionarioModel) -> VersionFuncionario:
    return VersionFuncionario(
        id=modelo.id,
        persona_id=modelo.persona_id,
        entidad_id=modelo.entidad_id,
        funcionario_id=modelo.funcionario_id,
        numero_version=modelo.numero_version,
        cargo=modelo.cargo,
        dependencia=modelo.dependencia,
        area=modelo.area,
        correo=modelo.correo,
        telefono=modelo.telefono,
        documento_id=modelo.documento_id,
        fecha_inicio=modelo.fecha_inicio,
        fecha_fin=modelo.fecha_fin,
        estado=modelo.estado,
        creado_en=modelo.creado_en,
    )


def a_modelo(
    version: VersionFuncionario, modelo: VersionFuncionarioModel | None = None
) -> VersionFuncionarioModel:
    modelo = modelo or VersionFuncionarioModel()
    modelo.id = version.id  # type: ignore[assignment]
    modelo.persona_id = version.persona_id
    modelo.entidad_id = version.entidad_id
    modelo.funcionario_id = version.funcionario_id
    modelo.numero_version = version.numero_version
    modelo.cargo = version.cargo
    modelo.dependencia = version.dependencia
    modelo.area = version.area
    modelo.correo = version.correo
    modelo.telefono = version.telefono
    modelo.documento_id = version.documento_id
    modelo.fecha_inicio = version.fecha_inicio
    modelo.fecha_fin = version.fecha_fin
    modelo.estado = version.estado
    return modelo
