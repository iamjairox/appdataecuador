"""Regla de dominio: Motor de Priorizacion -- Submodulo 6.11.

"No consultar todas las personas primero." Dado el cargo (mas relevante,
si una persona tiene varios) de una candidata a enriquecer, calcula una
prioridad numerica via fuzzy match contra el catalogo configurable (mismo
mecanismo que `clasificador_criticidad.py`, Modulo 5): cargos no
reconocidos reciben la prioridad por defecto (la mas baja), nunca quedan
fuera de la cola.
"""

from __future__ import annotations

from collections.abc import Callable

from rapidfuzz import fuzz

from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.rules.reglas_identidad import ReglasPriorizacion


def calcular_prioridad(cargo: str | None, reglas: ReglasPriorizacion) -> float:
    if not cargo or not cargo.strip():
        return reglas.prioridad_defecto

    cargo_normalizado = normalizar_texto(cargo)
    mejor_prioridad = reglas.prioridad_defecto
    mejor_score = 0.0
    for cargo_catalogo, prioridad in reglas.prioridad_por_cargo.items():
        score = fuzz.token_sort_ratio(cargo_normalizado, normalizar_texto(cargo_catalogo))
        if score >= reglas.umbral_score_minimo and score > mejor_score:
            mejor_score = score
            mejor_prioridad = prioridad
    return mejor_prioridad


def ordenar_por_prioridad[T](
    candidatos: list[T], obtener_cargo: Callable[[T], str | None], reglas: ReglasPriorizacion
) -> list[T]:
    """Ordena `candidatos` de mayor a menor prioridad (estable: candidatos
    con la misma prioridad conservan su orden relativo original)."""
    return sorted(candidatos, key=lambda c: calcular_prioridad(obtener_cargo(c), reglas), reverse=True)
