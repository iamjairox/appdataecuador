"""Mapper: EntidadModel <-> Entidad (dominio)."""

from __future__ import annotations

from govdata.domain.entities.entidad import Entidad
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel


def a_dominio(modelo: EntidadModel) -> Entidad:
    return Entidad(
        id=modelo.id,
        nombre=modelo.nombre,
        url_transparencia=modelo.url_transparencia,
        portal_origen=modelo.portal_origen,
        activo=modelo.activo,
        creado_en=modelo.creado_en,
        actualizado_en=modelo.actualizado_en,
        metadata_extra=dict(modelo.metadata_extra or {}),
    )


def a_modelo(entidad: Entidad, modelo: EntidadModel | None = None) -> EntidadModel:
    """Vuelca una entidad de dominio sobre un modelo ORM (nuevo o existente),
    para que SQLAlchemy sepa si es un INSERT o un UPDATE.
    """
    modelo = modelo or EntidadModel()
    if entidad.id is not None:
        modelo.id = entidad.id
    modelo.nombre = entidad.nombre
    modelo.url_transparencia = entidad.url_transparencia
    modelo.portal_origen = entidad.portal_origen
    modelo.activo = entidad.activo
    modelo.metadata_extra = dict(entidad.metadata_extra)
    return modelo
