"""Regla de dominio: seleccion del mes mas reciente publicado.

Pura y sin IO: no sabe nada de Playwright, HTTP ni HTML. Recibe la lista
de meses (1-12) que el adaptador de scraping encontro publicados para un
anio dado, y decide cual es "el ultimo". No asume posiciones fijas: no
importa el orden en que vengan los meses ni cuantos haya.

La iteracion "si el anio actual no tiene publicaciones, probar el anio
anterior" es responsabilidad del caso de uso (orquestacion), que llama al
puerto de scraping una vez por anio y usa esta regla para decidir sobre
cada respuesta.
"""

from __future__ import annotations

_MES_MINIMO = 1
_MES_MAXIMO = 12


def seleccionar_mes_mas_reciente(meses_publicados: list[int]) -> int | None:
    """Retorna el mes (1-12) mas alto de `meses_publicados`, o None si la
    lista esta vacia. Ignora silenciosamente valores fuera de rango
    (defensivo ante datos inconsistentes del portal).
    """
    meses_validos = [m for m in meses_publicados if _MES_MINIMO <= m <= _MES_MAXIMO]
    if not meses_validos:
        return None
    return max(meses_validos)
