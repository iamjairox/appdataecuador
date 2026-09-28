"""Regla de dominio: Scoring Engine -- Submodulo 6.3.

Compara dos `SenalesIdentidadDTO` campo por campo y produce un score
compuesto 0-100, con el detalle de cada campo (Submodulo 6.15,
trazabilidad de la propia decision). Los pesos son 100% configurables
(YAML, via `PesosScoring`) -- nada hardcodeado.

Un campo ausente en cualquiera de los dos lados (`None`) se trata como
"sin evidencia": `score_campo=0.0`, nunca se excluye del calculo (excluir
el peso reduciria artificialmente el umbral efectivo y facilitaria falsos
positivos con datos incompletos -- postura deliberadamente conservadora).
"""

from __future__ import annotations

from rapidfuzz import fuzz

from govdata.application.dto.identity_resolution_result_dto import CampoUtilizadoDTO
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.rules.reglas_identidad import PesosScoring


def _score_texto_difuso(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    return float(fuzz.token_sort_ratio(normalizar_texto(a), normalizar_texto(b)))


def _score_fingerprint(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 100.0
    return float(fuzz.ratio(a, b))


def _score_correo(a: str | None, b: str | None) -> float:
    """Coincidencia exacta -> evidencia fuerte. Mismo dominio (ej. ambos
    `@justicia.gob.ec`) -> evidencia debil (comparten institucion, no
    necesariamente persona) -- Submodulo 6.3 ("correo institucional,
    dominio del correo")."""
    if not a or not b:
        return 0.0
    a_norm, b_norm = a.strip().lower(), b.strip().lower()
    if a_norm == b_norm:
        return 100.0
    dominio_a = a_norm.rsplit("@", 1)[-1] if "@" in a_norm else None
    dominio_b = b_norm.rsplit("@", 1)[-1] if "@" in b_norm else None
    if dominio_a and dominio_a == dominio_b:
        return 30.0
    return 0.0


def _score_telefono(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    return 100.0 if a.strip() == b.strip() else 0.0


def calcular_score(
    a: SenalesIdentidadDTO, b: SenalesIdentidadDTO, pesos: PesosScoring
) -> tuple[float, list[CampoUtilizadoDTO]]:
    """Retorna `(score_total, campos_utilizados)`. `score_total` esta en
    el rango [0, 100] porque los pesos siempre suman 1.0 (validado en
    `PesosScoring.__post_init__`)."""
    definiciones: tuple[tuple[str, str | None, str | None, float, float], ...] = (
        ("fingerprint", a.fingerprint, b.fingerprint, _score_fingerprint(a.fingerprint, b.fingerprint), pesos.fingerprint),
        ("correo", a.correo, b.correo, _score_correo(a.correo, b.correo), pesos.correo),
        ("nombre", a.nombre, b.nombre, _score_texto_difuso(a.nombre, b.nombre), pesos.nombre),
        ("apellido", a.apellido, b.apellido, _score_texto_difuso(a.apellido, b.apellido), pesos.apellido),
        ("institucion", a.institucion, b.institucion, _score_texto_difuso(a.institucion, b.institucion), pesos.institucion),
        ("cargo", a.cargo, b.cargo, _score_texto_difuso(a.cargo, b.cargo), pesos.cargo),
    )
    telefono_score = _score_telefono(a.telefono, b.telefono)

    campos: list[CampoUtilizadoDTO] = []
    total = 0.0
    for campo, valor_a, valor_b, score_campo, peso in definiciones:
        aporte = score_campo * peso
        total += aporte
        campos.append(
            CampoUtilizadoDTO(
                campo=campo,
                valor_a=valor_a,
                valor_b=valor_b,
                coincide=score_campo >= 90.0,
                score_campo=round(score_campo, 2),
                peso=peso,
                aporte=round(aporte, 2),
            )
        )
    # Telefono no tiene peso propio en el catalogo oficial de la
    # especificacion (Fingerprint/Correo/Nombre/Apellido/Institucion/
    # Cargo); se reporta igualmente como campo informativo (score sin
    # peso) para trazabilidad, sin afectar el total.
    campos.append(
        CampoUtilizadoDTO(
            campo="telefono",
            valor_a=a.telefono,
            valor_b=b.telefono,
            coincide=telefono_score >= 90.0,
            score_campo=round(telefono_score, 2),
            peso=0.0,
            aporte=0.0,
        )
    )
    return round(total, 2), campos
