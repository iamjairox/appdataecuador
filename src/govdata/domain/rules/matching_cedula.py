"""Normalización y decisión conservadora de identidad para cédulas."""

from __future__ import annotations

import re
import unicodedata

from govdata.application.dto.identificacion_cedula_dto import (
    CedulaCandidateDTO,
    EstadoMatchingCedula,
    ResultadoMatchingCedulaDTO,
)


def normalizar_nombre(valor: str) -> str:
    sin_tildes = "".join(
        caracter for caracter in unicodedata.normalize("NFD", valor) if unicodedata.category(caracter) != "Mn"
    )
    return " ".join(re.sub(r"[^A-Za-z0-9 ]+", " ", sin_tildes.upper()).split())


def _tokens(valor: str) -> tuple[str, ...]:
    return tuple(normalizar_nombre(valor).split())


def hacer_matching_cedula(
    nombres: str, apellidos: str, candidatos: list[CedulaCandidateDTO]
) -> ResultadoMatchingCedulaDTO:
    """Selecciona solo una identidad inequívoca; empates siempre son ambiguos."""
    if not candidatos:
        return ResultadoMatchingCedulaDTO(estado=EstadoMatchingCedula.NO_CEDULA_FOUND)

    esperados = set(_tokens(f"{nombres} {apellidos}"))
    exactos: list[CedulaCandidateDTO] = []
    altos: list[tuple[float, CedulaCandidateDTO]] = []
    for candidato in candidatos:
        actual = set(_tokens(candidato.nombre_completo))
        if actual == esperados and actual:
            exactos.append(candidato)
            continue
        if actual:
            confianza = len(actual & esperados) / len(actual | esperados)
            if confianza >= 0.85 and actual.issubset(esperados) or confianza >= 0.90:
                altos.append((confianza, candidato))

    if len(exactos) == 1:
        return ResultadoMatchingCedulaDTO(EstadoMatchingCedula.MATCH_EXACT, exactos[0], 1.0, tuple(candidatos))
    if len(exactos) > 1:
        return ResultadoMatchingCedulaDTO(EstadoMatchingCedula.AMBIGUOUS, candidatos=tuple(exactos))
    if len(altos) == 1:
        confianza, candidato = altos[0]
        return ResultadoMatchingCedulaDTO(EstadoMatchingCedula.MATCH_HIGH_CONFIDENCE, candidato, confianza, tuple(candidatos))
    if len(altos) > 1:
        return ResultadoMatchingCedulaDTO(
            EstadoMatchingCedula.AMBIGUOUS, candidatos=tuple(candidato for _, candidato in altos)
        )
    return ResultadoMatchingCedulaDTO(EstadoMatchingCedula.NO_MATCH, candidatos=tuple(candidatos))
