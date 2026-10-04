"""Orden de fuentes públicas para resolver cédula por nombres."""

from __future__ import annotations

from govdata.application.ports.consulta_cedula_port import ConsultaCedulaPort
from govdata.infrastructure.scraping.playwright.consultasecuador_adapter import (
    ConsultaEcuadorAdapter,
)
from govdata.infrastructure.scraping.playwright.ecuadorlegalonline_adapter import (
    EcuadorLegalOnlineAdapter,
)
from govdata.infrastructure.scraping.playwright.misdatosecuador_adapter import (
    MisDatosEcuadorAdapter,
)
from govdata.infrastructure.scraping.playwright.senescyt_cedula_adapter import SenescytCedulaAdapter
from govdata.infrastructure.scraping.playwright.sri_adapter import SRIAdapter


def fuentes_consulta_cedula() -> list[ConsultaCedulaPort]:
    return [
        SRIAdapter(),
        ConsultaEcuadorAdapter(),
        MisDatosEcuadorAdapter(),
        EcuadorLegalOnlineAdapter(),
        SenescytCedulaAdapter(),
    ]
