"""Mapper: RegistroForoModel <-> RegistroForo (dominio)."""

from __future__ import annotations

from govdata.domain.entities.registro_foro import RegistroForo
from govdata.infrastructure.persistence.postgresql.models.registro_foro_model import (
    RegistroForoModel,
)


def a_dominio(modelo: RegistroForoModel) -> RegistroForo:
    return RegistroForo(
        id=modelo.id, persona_master_id=modelo.persona_master_id, clave_registro=modelo.clave_registro,
        nombre_completo=modelo.nombre_completo, registro=modelo.registro, provincia=modelo.provincia,
        estado=modelo.estado, cedula=modelo.cedula, correo_personal=modelo.correo_personal,
        celular_personal=modelo.celular_personal, numero_version=modelo.numero_version, vigente=modelo.vigente,
        fuente=modelo.fuente, fecha_consulta=modelo.fecha_consulta, nivel_confianza=modelo.nivel_confianza,
        version_fuente=modelo.version_fuente, evidencia=modelo.evidencia, creado_en=modelo.creado_en,
        actualizado_en=modelo.actualizado_en,
    )


def a_modelo(registro: RegistroForo, modelo: RegistroForoModel | None = None) -> RegistroForoModel:
    modelo = modelo or RegistroForoModel()
    if registro.id is not None:
        modelo.id = registro.id
    modelo.persona_master_id = registro.persona_master_id
    modelo.clave_registro = registro.clave_registro
    modelo.nombre_completo = registro.nombre_completo
    modelo.registro = registro.registro
    modelo.provincia = registro.provincia
    modelo.estado = registro.estado
    modelo.cedula = registro.cedula
    modelo.correo_personal = registro.correo_personal
    modelo.celular_personal = registro.celular_personal
    modelo.numero_version = registro.numero_version
    modelo.vigente = registro.vigente
    modelo.fuente = registro.fuente
    modelo.fecha_consulta = registro.fecha_consulta
    modelo.nivel_confianza = registro.nivel_confianza
    modelo.version_fuente = registro.version_fuente
    modelo.evidencia = registro.evidencia
    if registro.creado_en is not None:
        modelo.creado_en = registro.creado_en
    if registro.actualizado_en is not None:
        modelo.actualizado_en = registro.actualizado_en
    return modelo
