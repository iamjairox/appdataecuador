"""Mapper: FuncionarioModel <-> Funcionario (dominio)."""

from __future__ import annotations

from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.value_objects.cargo import Cargo
from govdata.infrastructure.persistence.postgresql.models.funcionario_model import FuncionarioModel


def a_dominio(modelo: FuncionarioModel) -> Funcionario:
    return Funcionario(
        id=modelo.id,
        persona_id=modelo.persona_id,
        entidad_id=modelo.entidad_id,
        cargo=Cargo(modelo.cargo),
        dependencia=modelo.dependencia,
        area_clasificada=modelo.area_clasificada,
        score_clasificacion=modelo.score_clasificacion,
        fecha_inicio=modelo.fecha_inicio,
        fecha_fin=modelo.fecha_fin,
        documento_id=modelo.documento_id,
        creado_en=modelo.creado_en,
        actualizado_en=modelo.actualizado_en,
    )


def a_modelo(funcionario: Funcionario, modelo: FuncionarioModel | None = None) -> FuncionarioModel:
    modelo = modelo or FuncionarioModel()
    if funcionario.id is not None:
        modelo.id = funcionario.id
    modelo.persona_id = funcionario.persona_id
    modelo.entidad_id = funcionario.entidad_id
    modelo.cargo = str(funcionario.cargo)
    modelo.dependencia = funcionario.dependencia
    modelo.area_clasificada = funcionario.area_clasificada
    modelo.score_clasificacion = funcionario.score_clasificacion
    modelo.fecha_inicio = funcionario.fecha_inicio
    modelo.fecha_fin = funcionario.fecha_fin
    modelo.documento_id = funcionario.documento_id
    return modelo
