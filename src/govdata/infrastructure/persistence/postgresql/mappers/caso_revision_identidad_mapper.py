"""Mapper: CasoRevisionIdentidadModel <-> CasoRevisionIdentidad (dominio)."""

from __future__ import annotations

from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad
from govdata.infrastructure.persistence.postgresql.models.caso_revision_identidad_model import (
    CasoRevisionIdentidadModel,
)


def a_dominio(modelo: CasoRevisionIdentidadModel) -> CasoRevisionIdentidad:
    return CasoRevisionIdentidad(
        uuid=modelo.id,
        persona_master_id_a=modelo.persona_master_id_a,
        persona_master_id_b=modelo.persona_master_id_b,
        registro_fuente_id=modelo.registro_fuente_id,
        score=modelo.score,
        explicacion=modelo.explicacion,
        campos_utilizados=tuple(modelo.campos_utilizados),
        estado=modelo.estado,
        creado_en=modelo.creado_en,
        resuelto_en=modelo.resuelto_en,
        resuelto_por=modelo.resuelto_por,
        criterio_resolucion=modelo.criterio_resolucion,
    )


def a_modelo(
    caso: CasoRevisionIdentidad, modelo: CasoRevisionIdentidadModel | None = None
) -> CasoRevisionIdentidadModel:
    modelo = modelo or CasoRevisionIdentidadModel()
    modelo.id = caso.uuid
    modelo.persona_master_id_a = caso.persona_master_id_a
    modelo.persona_master_id_b = caso.persona_master_id_b
    modelo.registro_fuente_id = caso.registro_fuente_id
    modelo.score = caso.score
    modelo.explicacion = caso.explicacion
    modelo.campos_utilizados = list(caso.campos_utilizados)
    modelo.estado = caso.estado
    modelo.creado_en = caso.creado_en
    modelo.resuelto_en = caso.resuelto_en
    modelo.resuelto_por = caso.resuelto_por
    modelo.criterio_resolucion = caso.criterio_resolucion
    return modelo
