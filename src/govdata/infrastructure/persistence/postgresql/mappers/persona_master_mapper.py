"""Mapper: PersonaMasterModel <-> PersonaMaster (dominio)."""

from __future__ import annotations

from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.telefono import Telefono
from govdata.infrastructure.persistence.postgresql.models.persona_master_model import (
    PersonaMasterModel,
)


def a_dominio(modelo: PersonaMasterModel) -> PersonaMaster:
    return PersonaMaster(
        id=modelo.id,
        uuid=modelo.uuid,
        persona_id=modelo.persona_id,
        nombre_completo=NombreCompleto(nombres=modelo.nombres, apellidos=modelo.apellidos),
        fingerprint_principal=modelo.fingerprint_principal,
        fingerprint_fonetico=modelo.fingerprint_fonetico,
        sexo=modelo.sexo,
        fecha_nacimiento=modelo.fecha_nacimiento,
        correo_principal=Correo.crear_opcional(modelo.correo_principal),
        telefono_principal=Telefono.crear_opcional(modelo.telefono_principal),
        estado=modelo.estado,
        nivel_confianza=modelo.nivel_confianza,
        cantidad_fuentes=modelo.cantidad_fuentes,
        cantidad_cargos_historicos=modelo.cantidad_cargos_historicos,
        fusionada_en_id=modelo.fusionada_en_id,
        creado_en=modelo.creado_en,
        actualizado_en=modelo.actualizado_en,
    )


def a_modelo(persona_master: PersonaMaster, modelo: PersonaMasterModel | None = None) -> PersonaMasterModel:
    modelo = modelo or PersonaMasterModel()
    if persona_master.id is not None:
        modelo.id = persona_master.id
    modelo.uuid = persona_master.uuid
    modelo.persona_id = persona_master.persona_id
    modelo.nombres = persona_master.nombre_completo.nombres
    modelo.apellidos = persona_master.nombre_completo.apellidos
    modelo.fingerprint_principal = persona_master.fingerprint_principal
    modelo.fingerprint_fonetico = persona_master.fingerprint_fonetico
    modelo.sexo = persona_master.sexo
    modelo.fecha_nacimiento = persona_master.fecha_nacimiento
    modelo.correo_principal = str(persona_master.correo_principal) if persona_master.correo_principal else None
    modelo.telefono_principal = (
        str(persona_master.telefono_principal) if persona_master.telefono_principal else None
    )
    modelo.estado = persona_master.estado
    modelo.nivel_confianza = persona_master.nivel_confianza
    modelo.cantidad_fuentes = persona_master.cantidad_fuentes
    modelo.cantidad_cargos_historicos = persona_master.cantidad_cargos_historicos
    modelo.fusionada_en_id = persona_master.fusionada_en_id
    if persona_master.creado_en is not None:
        modelo.creado_en = persona_master.creado_en
    if persona_master.actualizado_en is not None:
        modelo.actualizado_en = persona_master.actualizado_en
    return modelo
