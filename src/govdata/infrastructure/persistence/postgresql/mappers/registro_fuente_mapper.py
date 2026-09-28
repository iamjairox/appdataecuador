"""Mapper: RegistroFuenteModel <-> RegistroFuente (dominio)."""

from __future__ import annotations

from govdata.domain.entities.registro_fuente import RegistroFuente
from govdata.infrastructure.persistence.postgresql.models.registro_fuente_model import (
    RegistroFuenteModel,
)


def a_dominio(modelo: RegistroFuenteModel) -> RegistroFuente:
    return RegistroFuente(
        id=modelo.id,
        persona_master_id=modelo.persona_master_id,
        fuente=modelo.fuente,
        version=modelo.version,
        datos=modelo.datos,
        consultado_en=modelo.consultado_en,
        vigente=modelo.vigente,
        hash_contenido=modelo.hash_contenido,
    )


def a_modelo(registro: RegistroFuente, modelo: RegistroFuenteModel | None = None) -> RegistroFuenteModel:
    modelo = modelo or RegistroFuenteModel()
    if registro.id is not None:
        modelo.id = registro.id
    modelo.persona_master_id = registro.persona_master_id
    modelo.fuente = registro.fuente
    modelo.version = registro.version
    modelo.datos = registro.datos
    modelo.consultado_en = registro.consultado_en
    modelo.vigente = registro.vigente
    modelo.hash_contenido = registro.hash_contenido
    return modelo
