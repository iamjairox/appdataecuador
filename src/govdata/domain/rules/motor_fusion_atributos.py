"""Regla de dominio: Motor de Fusion (parte de atributos) -- Submodulos
6.14 (Fusion) y 6.15 (Trazabilidad).

"Si existen varias fuentes, consolidar. Nunca perder el origen." Dado el
conjunto completo de `AtributoTrazable` de una PersonaMaster (todas las
fuentes, todas las versiones), elige el valor GANADOR por campo (mayor
score; empate -> el mas reciente) para construir el perfil consolidado --
sin borrar ni modificar ningun `AtributoTrazable` perdedor: siguen
existiendo en la tabla completa como evidencia de procedencia.
"""

from __future__ import annotations

from govdata.domain.entities.atributo_trazable import AtributoTrazable


def seleccionar_atributos_ganadores(
    atributos: list[AtributoTrazable],
) -> dict[str, AtributoTrazable]:
    """Retorna `{campo: atributo_ganador}` -- uno por campo distinto
    presente en `atributos`."""
    ganadores: dict[str, AtributoTrazable] = {}
    for atributo in atributos:
        actual = ganadores.get(atributo.campo)
        if actual is None or _es_mejor(atributo, actual):
            ganadores[atributo.campo] = atributo
    return ganadores


def _es_mejor(candidato: AtributoTrazable, actual: AtributoTrazable) -> bool:
    if candidato.score != actual.score:
        return candidato.score > actual.score
    return candidato.obtenido_en > actual.obtenido_en
