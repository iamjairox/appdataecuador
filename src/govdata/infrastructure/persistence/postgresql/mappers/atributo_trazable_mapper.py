"""Mapper: AtributoTrazableModel <-> AtributoTrazable (dominio)."""

from __future__ import annotations

from govdata.domain.entities.atributo_trazable import AtributoTrazable
from govdata.infrastructure.persistence.postgresql.models.atributo_trazable_model import (
    AtributoTrazableModel,
)


def a_dominio(modelo: AtributoTrazableModel) -> AtributoTrazable:
    return AtributoTrazable(
        id=modelo.id,
        persona_master_id=modelo.persona_master_id,
        campo=modelo.campo,
        valor=modelo.valor,
        fuente=modelo.fuente,
        obtenido_en=modelo.obtenido_en,
        score=modelo.score,
        registro_fuente_id=modelo.registro_fuente_id,
    )


def a_modelo(atributo: AtributoTrazable, modelo: AtributoTrazableModel | None = None) -> AtributoTrazableModel:
    modelo = modelo or AtributoTrazableModel()
    if atributo.id is not None:
        modelo.id = atributo.id
    modelo.persona_master_id = atributo.persona_master_id
    modelo.campo = atributo.campo
    modelo.valor = atributo.valor
    modelo.fuente = atributo.fuente
    modelo.obtenido_en = atributo.obtenido_en
    modelo.score = atributo.score
    modelo.registro_fuente_id = atributo.registro_fuente_id
    return modelo
