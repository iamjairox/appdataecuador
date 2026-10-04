"""Regla de dominio: Clasificador Inteligente -- Submodulo 4.3.

Decide si una fila normalizada pertenece a un area especializada (Juridica o
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
    MotivoClasificacion,
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


def _contiene_palabra_clave(texto_normalizado: str, palabras_clave: list[str]) -> bool:
    """True si alguna palabra clave aparece como palabra(s) COMPLETA(s) --
    nunca substring: "LEGAL" no matchea "LEGALIZACION". Una clave de varias
    palabras ("ASESORIA LEGAL") exige esas palabras contiguas."""
    relleno = f" {texto_normalizado} "
    return any(f" {normalizar_texto(clave)} " in relleno for clave in palabras_clave if clave.strip())


def _coincide_por_palabra_clave(cargo_normalizado: str, reglas: ReglasClasificacion) -> str | None:
    """Respaldo del fuzzy match (`_mejor_coincidencia`): busca si alguna
    palabra clave configurada aparece como palabra completa en el cargo --
    ej. "ANALISTA JURIDICO 1 DEL SFPS" contiene "JURIDICO", aunque el fuzzy
    match contra "Asesor Juridico" no llegue al umbral por la diferencia
    de longitud."""
    for area, palabras_clave in reglas.palabras_clave_por_area.items():
        if _contiene_palabra_clave(cargo_normalizado, palabras_clave):
            return area
    return None


def _coincide_por_dependencia(
    cargo_normalizado: str, dependencia_normalizada: str, reglas: ReglasClasificacion
) -> str | None:
    """La dependencia identifica el area ("DIRECCION DE ASESORIA JURIDICA")
    solo si el cargo es un rol habilitante (director, analista...) -- ver
    `ReglasClasificacion.cargos_habilitantes_dependencia_por_area`."""
    if not dependencia_normalizada:
        return None
    for area, palabras_clave in reglas.palabras_clave_dependencia_por_area.items():
        habilitantes = reglas.cargos_habilitantes_dependencia_por_area.get(area, [])
        excluidos = reglas.cargos_excluidos_dependencia_por_area.get(area, [])
        if (
            _contiene_palabra_clave(dependencia_normalizada, palabras_clave)
            and _contiene_palabra_clave(cargo_normalizado, habilitantes)
            and not _contiene_palabra_clave(cargo_normalizado, excluidos)
        ):
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
    """Retorna el veredicto de clasificacion para toda fila con cargo.

    Cuando no hay coincidencia especializada, la fila se conserva como
    ``general``. Esto permite listar todos los contactos publicados por
    Transparencia sin ampliar el grupo que se consulta en fuentes externas.

    Tres mecanismos, en orden -- el primero que acierte gana:
    1. Fuzzy match contra `cargos_por_area` (el original, sin cambios).
    2. Respaldo por palabra clave (`_coincide_por_palabra_clave`): cubre
       cargos reales largos que el fuzzy match no alcanza (ver docstring
       de `ReglasClasificacion.palabras_clave_por_area`). Se reporta con
       `nivel_confianza=MEDIA` -- es una coincidencia exacta de token, no
       una aproximacion, pero tampoco paso por el fuzzy match para
       llamarla ALTA.
    3. Por dependencia (`_coincide_por_dependencia`): el cargo no nombra el
       area pero la unidad si, y el cargo es un rol habilitante. Se
       reporta con `nivel_confianza=BAJA`: la evidencia es indirecta.

    `motivo_clasificacion` deja constancia de cual mecanismo acerto.
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
                motivo_clasificacion=MotivoClasificacion.CARGO_SIMILAR,
            )

    area_por_palabra_clave = _coincide_por_palabra_clave(cargo_normalizado, reglas)
    if area_por_palabra_clave is not None:
        return FuncionarioClasificadoDTO(
            fila=fila,
            area=area_por_palabra_clave,
            cargo_normalizado=fila.cargo,
            score=reglas.umbral_score_minimo,
            nivel_confianza=NivelConfianzaClasificacion.MEDIA,
            motivo_clasificacion=MotivoClasificacion.CARGO_PALABRA_CLAVE,
        )

    area_por_dependencia = _coincide_por_dependencia(cargo_normalizado, normalizar_texto(fila.dependencia), reglas)
    if area_por_dependencia is not None:
        return FuncionarioClasificadoDTO(
            fila=fila,
            area=area_por_dependencia,
            cargo_normalizado=fila.cargo,
            score=reglas.umbral_score_minimo,
            nivel_confianza=NivelConfianzaClasificacion.BAJA,
            motivo_clasificacion=MotivoClasificacion.DEPENDENCIA,
        )

    return FuncionarioClasificadoDTO(
        fila=fila,
        area="general",
        cargo_normalizado=fila.cargo,
        score=0.0,
        nivel_confianza=NivelConfianzaClasificacion.BAJA,
        motivo_clasificacion=MotivoClasificacion.SIN_AREA_ESPECIALIZADA,
    )
