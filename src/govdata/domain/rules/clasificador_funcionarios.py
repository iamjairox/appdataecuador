"""Regla de dominio: Clasificador Inteligente -- Submodulo 4.3.

Decide si una fila normalizada pertenece a un area relevante (Juridica o
Financiera) comparando su cargo contra el catalogo configurable
(`ReglasClasificacion.cargos_por_area`, cargado desde
`config/rules/clasificacion_areas.yaml`). Solo `token_sort_ratio` (NO
`partial_ratio`) -- leccion aprendida en el Modulo 2: `partial_ratio` le
da 100 a cargos que son simple prefijo de la variante (ej. "Director"
solo vs "Director Juridico"), produciendo falsos positivos.
"""

from __future__ import annotations

from rapidfuzz import fuzz

from govdata.application.dto.fila_extraida_dto import FilaExtraidaDTO
from govdata.application.dto.funcionario_clasificado_dto import (
    FuncionarioClasificadoDTO,
    NivelConfianzaClasificacion,
)
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.rules.reglas_configurables import ReglasClasificacion


def _mejor_coincidencia(cargo_normalizado: str, reglas: ReglasClasificacion) -> tuple[str, str, float] | None:
    mejor_area: str | None = None
    mejor_cargo_candidato: str | None = None
    mejor_score = 0.0

    for area, cargos in reglas.cargos_por_area.items():
        for cargo_candidato in cargos:
            score = fuzz.token_sort_ratio(cargo_normalizado, normalizar_texto(cargo_candidato))
            if score > mejor_score:
                mejor_score, mejor_area, mejor_cargo_candidato = score, area, cargo_candidato

    if mejor_area is None or mejor_cargo_candidato is None:
        return None
    return mejor_area, mejor_cargo_candidato, mejor_score


def _coincide_por_palabra_clave(cargo_normalizado: str, reglas: ReglasClasificacion) -> str | None:
    """Respaldo del fuzzy match (`_mejor_coincidencia`): busca si alguna
    palabra clave configurada aparece como TOKEN COMPLETO (no substring)
    en el cargo -- ej. "ANALISTA JURIDICO 1 DEL SFPS" contiene el token
    "JURIDICO" exacto, aunque el fuzzy match contra "Asesor Juridico" no
    llegue al umbral por la diferencia de longitud. Solo token completo
    (nunca substring) para no capturar coincidencias parciales dentro de
    otra palabra."""
    tokens_cargo = set(cargo_normalizado.split())
    for area, palabras_clave in reglas.palabras_clave_por_area.items():
        for palabra_clave in palabras_clave:
            if normalizar_texto(palabra_clave) in tokens_cargo:
                return area
    return None


def _nivel_confianza(score: float, reglas: ReglasClasificacion) -> NivelConfianzaClasificacion:
    if score >= reglas.nivel_alta:
        return NivelConfianzaClasificacion.ALTA
    if score >= reglas.nivel_media:
        return NivelConfianzaClasificacion.MEDIA
    return NivelConfianzaClasificacion.BAJA


def clasificar_funcionario(
    fila: FilaExtraidaDTO, reglas: ReglasClasificacion
) -> FuncionarioClasificadoDTO | None:
    """Retorna el veredicto de clasificacion, o `None` si el cargo no
    supera `reglas.umbral_score_minimo` NI matchea por palabra clave (la
    fila se descarta -- NO se persisten funcionarios fuera de las areas
    relevantes).

    Dos mecanismos, en orden -- el primero que acierte gana:
    1. Fuzzy match contra `cargos_por_area` (el original, sin cambios).
    2. Respaldo por palabra clave (`_coincide_por_palabra_clave`): cubre
       cargos reales largos que el fuzzy match no alcanza (ver docstring
       de `ReglasClasificacion.palabras_clave_por_area`). Se reporta con
       `nivel_confianza=MEDIA` -- es una coincidencia exacta de token, no
       una aproximacion, pero tampoco paso por el fuzzy match para
       llamarla ALTA.
    """
    cargo_normalizado = normalizar_texto(fila.cargo)
    if not cargo_normalizado:
        return None

    coincidencia = _mejor_coincidencia(cargo_normalizado, reglas)
    if coincidencia is not None:
        area, cargo_candidato, score = coincidencia
        if score >= reglas.umbral_score_minimo:
            return FuncionarioClasificadoDTO(
                fila=fila,
                area=area,
                cargo_normalizado=cargo_candidato,
                score=score,
                nivel_confianza=_nivel_confianza(score, reglas),
            )

    area_por_palabra_clave = _coincide_por_palabra_clave(cargo_normalizado, reglas)
    if area_por_palabra_clave is not None:
        return FuncionarioClasificadoDTO(
            fila=fila,
            area=area_por_palabra_clave,
            cargo_normalizado=fila.cargo,
            score=reglas.umbral_score_minimo,
            nivel_confianza=NivelConfianzaClasificacion.MEDIA,
        )

    return None
