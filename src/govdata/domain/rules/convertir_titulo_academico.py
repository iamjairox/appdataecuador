"""Regla de dominio: conversion `TituloAcademico` (entidad persistida) ->
`PersonaAcademicaDTO` (Submodulo 7.3, el unico DTO) -- necesaria para que
el Comparador Academico (7.7) pueda tratar el estado ya guardado como el
lado "anterior" de la proxima comparacion, sin que el comparador conozca
la entidad de persistencia."""

from __future__ import annotations

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.domain.entities.titulo_academico import TituloAcademico
from govdata.domain.value_objects.estado_registro_academico import EstadoRegistroAcademico


def titulo_academico_a_dto(titulo: TituloAcademico) -> PersonaAcademicaDTO:
    # DESCONOCIDO es como `interpretar_estado_registro` (normalizador
    # academico) representa "sin informacion de estado" -- se vuelve a
    # `None` aqui para que el round-trip sea simetrico: una respuesta
    # fresca de SENESCYT sin campo `estado` (`None`) nunca debe compararse
    # como "distinta" de un titulo persistido cuyo estado tampoco se
    # conocia, o cada consulta identica generaria un falso CAMBIO_ESTADO.
    estado = None if titulo.estado == EstadoRegistroAcademico.DESCONOCIDO else titulo.estado.value

    return PersonaAcademicaDTO(
        titulo=titulo.titulo, nivel=titulo.nivel, institucion=titulo.institucion,
        fecha_registro=titulo.fecha_registro, pais=titulo.pais, estado=estado,
        modalidad=titulo.modalidad, numero_registro=titulo.numero_registro,
        area_conocimiento=titulo.area_conocimiento, tipo_titulo=titulo.tipo_titulo,
        fecha_graduacion=titulo.fecha_graduacion, observaciones=titulo.observaciones,
    )
