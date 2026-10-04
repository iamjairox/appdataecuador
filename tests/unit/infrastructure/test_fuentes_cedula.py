"""Tests: orden de fuentes de cedula -- SENESCYT primero por apellidos."""

from __future__ import annotations

from govdata.infrastructure.scraping.playwright.consultasecuador_adapter import (
    ConsultaEcuadorAdapter,
)
from govdata.infrastructure.scraping.playwright.ecuadorlegalonline_adapter import (
    EcuadorLegalOnlineAdapter,
)
from govdata.infrastructure.scraping.playwright.fuentes_cedula import fuentes_consulta_cedula
from govdata.infrastructure.scraping.playwright.misdatosecuador_adapter import (
    MisDatosEcuadorAdapter,
)
from govdata.infrastructure.scraping.playwright.senescyt_cedula_adapter import SenescytCedulaAdapter
from govdata.infrastructure.scraping.playwright.sri_adapter import SRIAdapter


def test_sri_es_la_primera_fuente() -> None:
    fuentes = fuentes_consulta_cedula()
    assert isinstance(fuentes[0], SRIAdapter)
    assert isinstance(fuentes[1], ConsultaEcuadorAdapter)
    assert isinstance(fuentes[2], MisDatosEcuadorAdapter)
    assert isinstance(fuentes[3], EcuadorLegalOnlineAdapter)
    assert isinstance(fuentes[4], SenescytCedulaAdapter)
    assert len(fuentes) == 5
