"""Mapper: OportunidadComercialModel <-> OportunidadComercial (dominio)."""

from __future__ import annotations

from govdata.domain.entities.oportunidad_comercial import OportunidadComercial
from govdata.infrastructure.persistence.postgresql.models.oportunidad_comercial_model import (
    OportunidadComercialModel,
)


def a_dominio(modelo: OportunidadComercialModel) -> OportunidadComercial:
    return OportunidadComercial(
        id=modelo.id,
        entidad_id=modelo.entidad_id,
        persona_id=modelo.persona_id,
        tipo=modelo.tipo,
        descripcion=modelo.descripcion,
        detectado_en=modelo.detectado_en,
        prioridad=modelo.prioridad,
    )


def a_modelo(
    oportunidad: OportunidadComercial, modelo: OportunidadComercialModel | None = None
) -> OportunidadComercialModel:
    modelo = modelo or OportunidadComercialModel()
    modelo.id = oportunidad.id
    modelo.entidad_id = oportunidad.entidad_id
    modelo.persona_id = oportunidad.persona_id
    modelo.tipo = oportunidad.tipo
    modelo.descripcion = oportunidad.descripcion
    modelo.detectado_en = oportunidad.detectado_en
    modelo.prioridad = oportunidad.prioridad
    return modelo
