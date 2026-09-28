"""Regla de dominio: seleccion del archivo de datos dentro de un numeral.

Cada numeral publicado trae varios archivos adjuntos (ej. "Conjunto de
datos", "Metadatos", "Diccionario"). Solo nos interesa el que contiene los
datos reales del directorio de personal -- nunca los metadatos ni el
diccionario de datos. Igual que en `matcher_item_documento`, se usa
matching difuso porque la descripcion real varia ("Conjunto de datos" vs
"1.Conjunto de datos", segun se verifico en el portal).
"""

from __future__ import annotations

from rapidfuzz import fuzz

from govdata.application.dto.descubrimiento_dto import ArchivoDTO, ResultadoMatchArchivoDTO
from govdata.domain.rules.normalizacion import normalizar_texto

UMBRAL_CONFIANZA_DEFECTO = 80.0
"""Se calibro contra casos reales: 'Metadatos' solo obtiene ~71 de
similitud contra la variante 'Datos' (comparten el sufijo). Un umbral de
80 separa con margen los verdaderos positivos (Conjunto de datos: 94-100)
de ese falso positivo, sin arriesgar rechazar variantes reales."""

VARIANTES_ARCHIVO_DATOS: tuple[str, ...] = (
    "Conjunto de datos",
    "Datos",
    "Data",
)

_VARIANTES_NORMALIZADAS = tuple(normalizar_texto(v) for v in VARIANTES_ARCHIVO_DATOS)


def _score_contra_variantes(texto_normalizado: str) -> float:
    """Similitud contra el catalogo de variantes. Solo `token_sort_ratio`
    -- ver el mismo razonamiento en `matcher_item_documento`: `partial_ratio`
    le da 100 a 'Metadatos' (contiene 'datos' como substring), lo cual es
    exactamente el falso positivo que NO queremos aceptar.
    """
    if not texto_normalizado:
        return 0.0
    return max(fuzz.token_sort_ratio(texto_normalizado, variante) for variante in _VARIANTES_NORMALIZADAS)


def seleccionar_archivo_datos(
    archivos: list[ArchivoDTO], umbral: float = UMBRAL_CONFIANZA_DEFECTO
) -> ResultadoMatchArchivoDTO | None:
    """Retorna el archivo cuya descripcion mejor coincide con "Conjunto de
    datos", o None si ninguno supera el umbral (ej. el numeral solo trae
    Metadatos/Diccionario, sin datos reales).
    """
    mejor: ResultadoMatchArchivoDTO | None = None
    for archivo in archivos:
        score = _score_contra_variantes(normalizar_texto(archivo.descripcion))
        if mejor is None or score > mejor.score:
            mejor = ResultadoMatchArchivoDTO(archivo=archivo, score=score)

    if mejor is None or mejor.score < umbral:
        return None
    return mejor
