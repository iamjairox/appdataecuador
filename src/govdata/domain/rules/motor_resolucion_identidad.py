"""Regla de dominio: Identity Resolution Engine -- Submodulo 6.2.

Decide, entre un conjunto acotado de candidatas (acotarlo es
responsabilidad del repositorio -- ej. por fingerprint/correo -- NUNCA de
este motor, que no hace IO), cual es la mejor coincidencia para unas
senales nuevas, usando el Scoring Engine (Submodulo 6.3) sobre MULTIPLES
senales a la vez: "nunca unicamente el nombre".

Nunca decide fusionar -- solo informa el mejor candidato y su score. La
decision de que hacer con ese score (fusionar automaticamente, crear un
caso de revision manual, o mantener separado) es responsabilidad del
Submodulo 6.21 (`motor_confianza_fusion.py`), deliberadamente separado.
"""

from __future__ import annotations

from govdata.application.dto.identity_resolution_result_dto import (
    CampoUtilizadoDTO,
    IdentityResolutionResultDTO,
)
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.domain.rules.motor_scoring_identidad import calcular_score
from govdata.domain.rules.reglas_identidad import PesosScoring

_UMBRAL_NIVEL_ALTA = 90.0
_UMBRAL_NIVEL_MEDIA = 75.0


def _nivel_confianza_descriptivo(score: float) -> str:
    if score >= _UMBRAL_NIVEL_ALTA:
        return "alta"
    if score >= _UMBRAL_NIVEL_MEDIA:
        return "media"
    return "baja"


def _explicar(score: float, campos: list[CampoUtilizadoDTO]) -> str:
    coincidencias = [c.campo for c in campos if c.coincide and c.peso > 0]
    diferencias = [c.campo for c in campos if not c.coincide and c.peso > 0 and (c.valor_a or c.valor_b)]
    partes = [f"score={score:.2f}"]
    if coincidencias:
        partes.append("coincide en: " + ", ".join(coincidencias))
    if diferencias:
        partes.append("difiere en: " + ", ".join(diferencias))
    return "; ".join(partes)


def resolver_identidad(
    senales_nuevas: SenalesIdentidadDTO,
    candidatas: list[tuple[int, SenalesIdentidadDTO]],
    pesos: PesosScoring,
) -> IdentityResolutionResultDTO:
    """Retorna el mejor veredicto entre `candidatas` para `senales_nuevas`.

    `candidatas` es `(persona_master_id, senales)`. Si esta vacia, o
    ninguna candidata alcanza `pesos.umbral_minimo_coincidencia`, retorna
    `persona_master_id=None` (sin coincidencia) -- nunca se asume una
    identidad por defecto.
    """
    if not candidatas:
        return IdentityResolutionResultDTO(
            persona_master_id=None,
            score=0.0,
            nivel_confianza="baja",
            explicacion="No hay candidatas para comparar",
            motivo="sin_candidatas",
            campos_utilizados=[],
        )

    mejor_id: int | None = None
    mejor_score = -1.0
    mejor_campos: list[CampoUtilizadoDTO] = []
    for candidato_id, senales_candidata in candidatas:
        score, campos = calcular_score(senales_nuevas, senales_candidata, pesos)
        if score > mejor_score:
            mejor_id, mejor_score, mejor_campos = candidato_id, score, campos

    if mejor_score < pesos.umbral_minimo_coincidencia:
        return IdentityResolutionResultDTO(
            persona_master_id=None,
            score=mejor_score,
            nivel_confianza=_nivel_confianza_descriptivo(mejor_score),
            explicacion=_explicar(mejor_score, mejor_campos),
            motivo="score_bajo_umbral_minimo",
            campos_utilizados=mejor_campos,
        )

    return IdentityResolutionResultDTO(
        persona_master_id=mejor_id,
        score=mejor_score,
        nivel_confianza=_nivel_confianza_descriptivo(mejor_score),
        explicacion=_explicar(mejor_score, mejor_campos),
        motivo="mejor_candidata_seleccionada",
        campos_utilizados=mejor_campos,
    )
