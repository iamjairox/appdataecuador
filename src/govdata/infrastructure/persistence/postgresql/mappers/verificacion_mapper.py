"""Mapper: VerificacionModel <-> Verificacion (dominio)."""

from __future__ import annotations

from govdata.domain.entities.verificacion import Verificacion
from govdata.infrastructure.persistence.postgresql.models.verificacion_model import (
    VerificacionModel,
)


def a_dominio(modelo: VerificacionModel) -> Verificacion:
    return Verificacion(
        id=modelo.id,
        entidad_id=modelo.entidad_id,
        documento_id=modelo.documento_id,
        hubo_cambio=modelo.hubo_cambio,
        motivo=modelo.motivo,
        hash_verificado=modelo.hash_verificado,
        verificado_en=modelo.verificado_en,
    )


def a_modelo(verificacion: Verificacion, modelo: VerificacionModel | None = None) -> VerificacionModel:
    modelo = modelo or VerificacionModel()
    modelo.id = verificacion.id  # type: ignore[assignment]
    modelo.entidad_id = verificacion.entidad_id
    modelo.documento_id = verificacion.documento_id
    modelo.hubo_cambio = verificacion.hubo_cambio
    modelo.motivo = verificacion.motivo
    modelo.hash_verificado = verificacion.hash_verificado
    modelo.verificado_en = verificacion.verificado_en
    return modelo
