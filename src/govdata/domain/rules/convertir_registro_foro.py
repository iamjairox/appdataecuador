"""Regla de dominio: conversion `RegistroForo` (entidad persistida) ->
`RegistroForoDTO` (Submodulo 8.1, el unico DTO) -- necesaria para que el
Comparador Foro (8.5) pueda tratar el estado ya guardado como el lado
"anterior" de la proxima comparacion, sin que el comparador conozca la
entidad de persistencia. Mismo rol que `convertir_titulo_academico.py`
(Modulo 7)."""

from __future__ import annotations

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.domain.entities.registro_foro import RegistroForo
from govdata.domain.value_objects.estado_registro_foro import EstadoRegistroForo


def registro_foro_a_dto(registro: RegistroForo) -> RegistroForoDTO:
    # DESCONOCIDO -> None por el mismo motivo que en
    # `convertir_titulo_academico.py` (Modulo 7): una respuesta fresca
    # del Foro sin campo `estado` (`None`) nunca debe compararse como
    # "distinta" de un registro persistido cuyo estado tampoco se
    # conocia, o cada consulta identica generaria un falso CAMBIO_ESTADO.
    estado = None if registro.estado == EstadoRegistroForo.DESCONOCIDO else registro.estado.value

    return RegistroForoDTO(
        nombre_completo=registro.nombre_completo, registro=registro.registro,
        provincia=registro.provincia, estado=estado, cedula=registro.cedula,
    )
