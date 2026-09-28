"""Tests: NivelPrioridadEjecucion -- Submodulo 9.5 (catalogo + comparador)."""

from __future__ import annotations

from govdata.domain.value_objects.nivel_prioridad_ejecucion import (
    NivelPrioridadEjecucion,
    es_mas_prioritario,
)


class TestEsMasPrioritario:
    def test_muy_alta_es_mas_prioritaria_que_baja(self) -> None:
        assert es_mas_prioritario(NivelPrioridadEjecucion.MUY_ALTA, NivelPrioridadEjecucion.BAJA) is True

    def test_baja_no_es_mas_prioritaria_que_muy_alta(self) -> None:
        assert es_mas_prioritario(NivelPrioridadEjecucion.BAJA, NivelPrioridadEjecucion.MUY_ALTA) is False

    def test_mismo_nivel_no_es_mas_prioritario(self) -> None:
        assert es_mas_prioritario(NivelPrioridadEjecucion.MEDIA, NivelPrioridadEjecucion.MEDIA) is False
