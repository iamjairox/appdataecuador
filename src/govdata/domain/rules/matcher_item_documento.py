"""Regla de dominio: matching difuso del numeral "Directorio y distributivo
del personal".

El texto exacto varia entre entidades y a lo largo del tiempo (se
verifico contra el portal real: "Directorio y distributivo personal de la
entidad" en vez del texto de referencia "Directorio y distributivo del
personal"). Esta regla NUNCA compara con `==`; siempre usa similitud
difusa (RapidFuzz) contra un catalogo de variantes conocidas, y exige un
umbral minimo de confianza antes de aceptar una coincidencia.
"""

from __future__ import annotations

from rapidfuzz import fuzz

from govdata.application.dto.descubrimiento_dto import NumeralPublicadoDTO, ResultadoMatchNumeralDTO
from govdata.domain.rules.normalizacion import normalizar_texto

UMBRAL_CONFIANZA_DEFECTO = 70.0

VARIANTES_DIRECTORIO_PERSONAL: tuple[str, ...] = (
    "Directorio y distributivo del personal",
    "Directorio y distributivo personal de la entidad",
    "Directorio del personal",
    "Distributivo del personal",
    "Directorio y distributivo",
    "Directorio y distributivo de personal",
)

_VARIANTES_NORMALIZADAS = tuple(normalizar_texto(v) for v in VARIANTES_DIRECTORIO_PERSONAL)


def _score_contra_variantes(texto_normalizado: str) -> float:
    """Similitud contra el catalogo de variantes conocidas.

    Se usa deliberadamente SOLO `token_sort_ratio` (compara las frases
    completas, tolerante a orden de palabras) y NO `partial_ratio`:
    `partial_ratio` da 100 cuando el texto candidato es un simple prefijo
    de la variante (ej. "Directorio" solo, sin "y distributivo del
    personal"), lo que produciria falsos positivos con numerales que nada
    tienen que ver (ej. un futuro "Directorio Telefonico Institucional").
    """
    if not texto_normalizado:
        return 0.0
    return max(fuzz.token_sort_ratio(texto_normalizado, variante) for variante in _VARIANTES_NORMALIZADAS)


def seleccionar_numeral_directorio_personal(
    numerales: list[NumeralPublicadoDTO], umbral: float = UMBRAL_CONFIANZA_DEFECTO
) -> ResultadoMatchNumeralDTO | None:
    """Retorna el numeral cuya descripcion mejor coincide con "Directorio y
    distributivo del personal" (y sus variantes conocidas), siempre que su
    score supere `umbral`. Si ningun numeral alcanza el umbral, retorna
    None (el caso de uso debe tratarlo como "documento no encontrado",
    nunca elegir el mejor candidato a la fuerza).
    """
    mejor: ResultadoMatchNumeralDTO | None = None
    for numeral in numerales:
        score = _score_contra_variantes(normalizar_texto(numeral.descripcion))
        if mejor is None or score > mejor.score:
            mejor = ResultadoMatchNumeralDTO(numeral=numeral, score=score)

    if mejor is None or mejor.score < umbral:
        return None
    return mejor
