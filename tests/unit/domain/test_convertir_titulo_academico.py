"""Tests: conversion TituloAcademico -> PersonaAcademicaDTO (round-trip
usado por el Comparador Academico, Submodulo 7.7)."""

from __future__ import annotations

from govdata.domain.entities.titulo_academico import TituloAcademico
from govdata.domain.rules.convertir_titulo_academico import titulo_academico_a_dto
from govdata.domain.value_objects.estado_registro_academico import EstadoRegistroAcademico


def _titulo(**kwargs) -> TituloAcademico:
    base = {"persona_master_id": 1, "clave_titulo": "x", "titulo": "ABOGADO", "nivel": "TERCER NIVEL", "institucion": "UCE"}
    base.update(kwargs)
    return TituloAcademico(**base)


class TestTituloAcademicoADto:
    def test_estado_desconocido_se_convierte_a_none(self) -> None:
        """Regresion: sin este mapeo, comparar una respuesta fresca sin
        campo `estado` (None) contra un titulo persistido con el DEFECTO
        `DESCONOCIDO` generaria un falso CAMBIO_ESTADO en cada consulta."""
        titulo = _titulo(estado=EstadoRegistroAcademico.DESCONOCIDO)
        dto = titulo_academico_a_dto(titulo)
        assert dto.estado is None

    def test_estado_conocido_se_preserva(self) -> None:
        titulo = _titulo(estado=EstadoRegistroAcademico.VIGENTE)
        dto = titulo_academico_a_dto(titulo)
        assert dto.estado == "vigente"

    def test_numero_registro_se_preserva(self) -> None:
        titulo = _titulo(numero_registro="REG-1")
        dto = titulo_academico_a_dto(titulo)
        assert dto.numero_registro == "REG-1"
