"""Normalización y decisión conservadora de identidad para cédulas.

El matching es deliberadamente conservador:
- Nunca se selecciona automáticamente el primer resultado
- Si hay dos candidatos plausibles, el resultado es AMBIGUOUS
- La identidad se basa en comparación normalizada del nombre completo,
  no solo en la división heurística

Ejemplo:
    Entrada: "DEXI VIRGINIA AYALA SANTI"
    Candidatos:
        - "AYALA SANTI ALEXANDER RAFAEL"
        - "AYALA SANTI DEXI VIRGINIA"
        - "AYALA SANTI KEVIN XAVIER"
    Resultado: MATCH_HIGH_CONFIDENCE con "AYALA SANTI DEXI VIRGINIA"
"""

from __future__ import annotations

import re
import unicodedata

from govdata.application.dto.identificacion_cedula_dto import (
    CedulaCandidateDTO,
    EstadoMatchingCedula,
    ResultadoMatchingCedulaDTO,
)


def normalizar_nombre(valor: str) -> str:
    """Normaliza un nombre para comparación: mayúsculas, sin tildes, sin puntuación."""
    sin_tildes = "".join(
        caracter for caracter in unicodedata.normalize("NFD", valor) if unicodedata.category(caracter) != "Mn"
    )
    return " ".join(re.sub(r"[^A-Za-z0-9 ]+", " ", sin_tildes.upper()).split())


def _tokens(valor: str) -> tuple[str, ...]:
    """Divide un nombre en tokens normalizados."""
    return tuple(normalizar_nombre(valor).split())


def _similaridad_jaccard(conjunto_a: set[str], conjunto_b: set[str]) -> float:
    """Calcula la similitud de Jaccard entre dos conjuntos de tokens."""
    if not conjunto_a or not conjunto_b:
        return 0.0
    interseccion = len(conjunto_a & conjunto_b)
    union = len(conjunto_a | conjunto_b)
    return interseccion / union if union > 0 else 0.0


def _similaridad_orden(texto_a: str, texto_b: str) -> float:
    """Calcula la similitud considerando el orden de las palabras.

    Dos nombres con las mismas palabras pero en diferente orden tienen
    una similitud alta pero no perfecta (ej. "DEXI VIRGINIA AYALA SANTI"
    vs "AYALA SANTI DEXI VIRGINIA").
    """
    tokens_a = _tokens(texto_a)
    tokens_b = _tokens(texto_b)

    if not tokens_a or not tokens_b:
        return 0.0

    # Si son exactamente iguales (mismo orden), similitud perfecta
    if tokens_a == tokens_b:
        return 1.0

    # Si tienen las mismas palabras pero diferente orden, similitud alta
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if set_a == set_b:
        return 0.95

    # Si no, usar Jaccard
    return _similaridad_jaccard(set_a, set_b)


def hacer_matching_cedula(
    nombres: str, apellidos: str, candidatos: list[CedulaCandidateDTO]
) -> ResultadoMatchingCedulaDTO:
    """Selecciona solo una identidad inequívoca; empates siempre son ambiguos.

    La comparación se hace sobre el nombre completo normalizado, no solo
    sobre la división heurística entre nombres y apellidos.
    """
    if not candidatos:
        return ResultadoMatchingCedulaDTO(estado=EstadoMatchingCedula.NO_CEDULA_FOUND)

    nombre_completo_esperado = f"{nombres} {apellidos}".strip()
    tokens_esperados = set(_tokens(nombre_completo_esperado))

    exactos: list[CedulaCandidateDTO] = []
    altos: list[tuple[float, CedulaCandidateDTO]] = []

    for candidato in candidatos:
        tokens_candidato = set(_tokens(candidato.nombre_completo))

        # Comparación exacta de tokens (sin importar el orden)
        if tokens_candidato == tokens_esperados and tokens_candidato:
            exactos.append(candidato)
            continue

        # Comparación difusa
        if tokens_candidato:
            # Usar similitud de Jaccard para tokens
            confianza_jaccard = _similaridad_jaccard(tokens_esperados, tokens_candidato)

            # Usar similitud de orden para el nombre completo
            confianza_orden = _similaridad_orden(
                nombre_completo_esperado, candidato.nombre_completo
            )

            # Tomar el máximo de ambas similitudes
            confianza = max(confianza_jaccard, confianza_orden)

            # Umbrales conservadores
            if confianza >= 0.90:
                altos.append((confianza, candidato))

    # Decisión conservadora
    if len(exactos) == 1:
        return ResultadoMatchingCedulaDTO(
            estado=EstadoMatchingCedula.MATCH_EXACT,
            candidato=exactos[0],
            confianza=1.0,
            candidatos=tuple(candidatos),
        )
    if len(exactos) > 1:
        return ResultadoMatchingCedulaDTO(
            estado=EstadoMatchingCedula.AMBIGUOUS,
            candidatos=tuple(exactos),
        )
    if len(altos) == 1:
        confianza, candidato = altos[0]
        return ResultadoMatchingCedulaDTO(
            estado=EstadoMatchingCedula.MATCH_HIGH_CONFIDENCE,
            candidato=candidato,
            confianza=confianza,
            candidatos=tuple(candidatos),
        )
    if len(altos) > 1:
        return ResultadoMatchingCedulaDTO(
            estado=EstadoMatchingCedula.AMBIGUOUS,
            candidatos=tuple(candidato for _, candidato in altos),
        )
    return ResultadoMatchingCedulaDTO(
        estado=EstadoMatchingCedula.NO_MATCH,
        candidatos=tuple(candidatos),
    )
