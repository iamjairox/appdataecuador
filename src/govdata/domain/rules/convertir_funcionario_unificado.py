"""Regla de dominio: conversion Funcionario+Persona (Modulo 4, ya
persistidos) -> `FuncionarioUnificadoDTO` (el contrato oficial).

Usada por el Modulo 5 para reconstruir el snapshot "anterior" de
funcionarios desde lo YA persistido (necesario para poder comparar contra
la version actual sin volver a extraer el documento viejo). Es
deliberadamente una funcion NUEVA y propia del Modulo 5 -- existe una
conversion equivalente dentro de `ConsultaService._a_dto` (Modulo 4), pero
esa es codigo YA APROBADO que no debe tocarse; duplicar estas ~10 lineas
es preferible a modificar un modulo previamente cerrado.
"""

from __future__ import annotations

from govdata.application.dto.resultado_unificado_dto import FuncionarioUnificadoDTO
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.persona import Persona


def funcionario_a_unificado(funcionario: Funcionario, persona: Persona) -> FuncionarioUnificadoDTO:
    return FuncionarioUnificadoDTO(
        nombre=persona.nombre_completo.nombres,
        apellido=persona.nombre_completo.apellidos,
        cargo=str(funcionario.cargo),
        dependencia=funcionario.dependencia,
        correo=str(persona.correo) if persona.correo else None,
        telefono=str(persona.telefono) if persona.telefono else None,
        area=funcionario.area_clasificada.value,
        score=round(funcionario.score_clasificacion or 0.0, 2),
        fingerprint=persona.fingerprint or "",
    )
