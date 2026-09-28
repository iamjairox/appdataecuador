"""Regla de dominio: Motor de Politicas de Ejecucion -- mejora sugerida
por el cliente al cierre del Modulo 8.

"En lugar de que el orquestador tenga reglas fijas, definiria politicas
configurables... seleccionables por el orquestador." Esta funcion es la
UNICA puerta de entrada al catalogo -- nunca se lee `politicas_por_nombre`
directamente fuera de aqui, para que un nombre de politica invalido
falle siempre de la misma forma explicita en vez de un `KeyError` crudo
en algun lugar inesperado."""

from __future__ import annotations

from govdata.domain.exceptions.domain_exceptions import PoliticaEjecucionInvalidaError
from govdata.domain.rules.reglas_orquestador import CatalogoPoliticas, PoliticaEjecucion


def resolver_politica(nombre: str, catalogo: CatalogoPoliticas) -> PoliticaEjecucion:
    politica = catalogo.obtener(nombre)
    if politica is None:
        disponibles = ", ".join(sorted(catalogo.politicas_por_nombre)) or "(ninguna configurada)"
        raise PoliticaEjecucionInvalidaError(f"Politica de ejecucion desconocida: '{nombre}'. Disponibles: {disponibles}")
    return politica
