"""Mapper: PublicacionModel <-> PublicacionMensual (dominio)."""

from __future__ import annotations

from govdata.domain.entities.publicacion import PublicacionMensual
from govdata.infrastructure.persistence.postgresql.models.publicacion_model import PublicacionModel


def a_dominio(modelo: PublicacionModel) -> PublicacionMensual:
    return PublicacionMensual(
        id=modelo.id,
        entidad_id=modelo.entidad_id,
        mes_publicado=modelo.mes_publicado,
        url_item=modelo.url_item,
        detectado_en=modelo.detectado_en,
    )


def a_modelo(publicacion: PublicacionMensual, modelo: PublicacionModel | None = None) -> PublicacionModel:
    modelo = modelo or PublicacionModel()
    if publicacion.id is not None:
        modelo.id = publicacion.id
    modelo.entidad_id = publicacion.entidad_id
    modelo.mes_publicado = publicacion.mes_publicado
    modelo.url_item = publicacion.url_item
    return modelo
