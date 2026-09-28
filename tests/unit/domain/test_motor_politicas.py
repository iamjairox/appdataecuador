"""Tests: Motor de Politicas de Ejecucion (mejora sugerida por el cliente)."""

from __future__ import annotations

import pytest

from govdata.domain.exceptions.domain_exceptions import PoliticaEjecucionInvalidaError
from govdata.domain.rules.motor_politicas import resolver_politica
from govdata.domain.rules.reglas_orquestador import CatalogoPoliticas, PoliticaEjecucion

_CATALOGO = CatalogoPoliticas(
    politicas_por_nombre={
        "consulta_rapida": PoliticaEjecucion(nombre="consulta_rapida"),
        "actualizacion_completa": PoliticaEjecucion(nombre="actualizacion_completa", forzar_actualizacion=True),
    }
)


class TestResolverPolitica:
    def test_resuelve_politica_existente(self) -> None:
        politica = resolver_politica("actualizacion_completa", _CATALOGO)
        assert politica.forzar_actualizacion is True

    def test_politica_desconocida_lanza_error_explicito(self) -> None:
        with pytest.raises(PoliticaEjecucionInvalidaError):
            resolver_politica("no_existe", _CATALOGO)
