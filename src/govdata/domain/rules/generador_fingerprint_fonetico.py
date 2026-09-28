"""Regla de dominio: generador de fingerprint fonetico -- Submodulo 6.1 /
6.2 (segunda senal de matching de identidad, complementaria al
fingerprint exacto de `generador_fingerprint.py`, Modulo 4).

El fingerprint exacto (Modulo 4) detecta la MISMA escritura de un nombre.
No detecta variantes de transcripcion fonetica entre fuentes distintas,
frecuentes en registros publicos ecuatorianos:

    "VASQUEZ"  vs "BASQUEZ"    (V/B se pronuncian igual en espanol)
    "GONZALES" vs "GONZALEZ"   (S/Z finales se pronuncian igual)
    "HERRERA"  vs "ERRERA"     (H es muda)
    "SILLA"    vs "SIYA"       (LL se pronuncia como Y en gran parte de
                                 Ecuador -- yeismo)

Esta clave fonetica SIMPLIFICADA (no es un Soundex/Metaphone formal, es
una reduccion de equivalencias fonemicas comunes del espanol) normaliza
esas variantes a una unica representacion, de forma pura y determinista.

Deliberadamente NO decide por si sola si dos personas son la misma --
es UNA senal mas entre varias que consume el Scoring Engine (Submodulo
6.3); nunca se usa aislada ("nunca unicamente el nombre").
"""

from __future__ import annotations

import re

from govdata.domain.rules.normalizacion import normalizar_texto

_SUSTITUCIONES: tuple[tuple[str, str], ...] = (
    ("LL", "Y"),
    ("QU", "K"),
    ("CE", "SE"),
    ("CI", "SI"),
    ("GE", "JE"),
    ("GI", "JI"),
    ("CH", "X"),
    ("C", "K"),
    ("H", ""),
    ("V", "B"),
    ("Z", "S"),
    ("W", "B"),
)


def _colapsar_repetidos(texto: str) -> str:
    return re.sub(r"(.)\1+", r"\1", texto)


def _reducir_fonetica(palabra: str) -> str:
    resultado = palabra
    for origen, destino in _SUSTITUCIONES:
        resultado = resultado.replace(origen, destino)
    return _colapsar_repetidos(resultado)


def generar_fingerprint_fonetico(nombres: str, apellidos: str) -> str:
    """Retorna la clave fonetica combinada de nombres + apellidos.

    Misma disciplina que `generar_fingerprint` (Modulo 4): pura, sin IO,
    misma entrada siempre produce la misma salida.
    """
    nombres_norm = normalizar_texto(nombres).replace(" ", "")
    apellidos_norm = normalizar_texto(apellidos).replace(" ", "")
    return _reducir_fonetica(nombres_norm) + _reducir_fonetica(apellidos_norm)
