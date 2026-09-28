"""Servicio: MotorPoliticasService -- Motor de Politicas de Ejecucion
(mejora sugerida por el cliente al cierre del Modulo 8)."""

from __future__ import annotations

from govdata.domain.rules.motor_politicas import resolver_politica
from govdata.domain.rules.reglas_orquestador import CatalogoPoliticas, PoliticaEjecucion


class MotorPoliticasService:
    def __init__(self, catalogo: CatalogoPoliticas) -> None:
        self._catalogo = catalogo

    def resolver(self, nombre: str) -> PoliticaEjecucion:
        return resolver_politica(nombre, self._catalogo)

    def listar_disponibles(self) -> list[str]:
        return sorted(self._catalogo.politicas_por_nombre)
