"""Tests para el adaptador del Foro de Abogados de la Función Judicial."""

from __future__ import annotations

import pytest

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.infrastructure.scraping.playwright.foro_abogados_adapter import (
    ForoAbogadosPlaywrightAdapter,
    SelectoresForoAbogados,
    FuenteForoNoDisponibleError,
)
from govdata.infrastructure.scraping.playwright.selectors import foro_abogados_selectors


class TestSelectoresForoAbogados:
    """Tests para los selectores centralizados."""

    def test_selectores_por_defecto(self) -> None:
        selectores = SelectoresForoAbogados()
        assert selectores.input_cedula == "#CEDULA"
        assert selectores.boton_ceptar == "#btnValidarReg"
        assert selectores.tabla_resultados == "table"
        assert selectores.filas_resultados == "table tbody tr"

    def test_url_consulta(self) -> None:
        assert (
            foro_abogados_selectors.URL_CONSULTA
            == "https://app.funcionjudicial.gob.ec/ForoAbogados/Login/frmCheckCodigoRegistro.jsp"
        )


class TestForoAbogadosPlaywrightAdapter:
    """Tests para el adaptador del Foro de Abogados."""

    def test_inicializacion(self) -> None:
        adapter = ForoAbogadosPlaywrightAdapter()
        assert adapter._selectores is not None
        assert adapter._timeout_ms == 30_000
        assert adapter._headless is True

    def test_detectar_captcha(self) -> None:
        adapter = ForoAbogadosPlaywrightAdapter()
        assert adapter._detectar_captcha("captcha") is True
        assert adapter._detectar_captcha("recaptcha") is True
        assert adapter._detectar_captcha("g-recaptcha") is True
        assert adapter._detectar_captcha("challenge") is True
        assert adapter._detectar_captcha("just a moment") is True
        assert adapter._detectar_captcha("normal content") is False

    def test_buscar_por_persona_no_soportado(self) -> None:
        """El Foro de Abogados solo permite búsqueda por cédula, no por nombre."""
        adapter = ForoAbogadosPlaywrightAdapter()
        with pytest.raises(FuenteForoNoDisponibleError):
            adapter.buscar_por_persona(None)  # type: ignore

    def test_buscar_por_persona_master_no_soportado(self) -> None:
        """El Foro de Abogados solo permite búsqueda por cédula, no por nombre."""
        adapter = ForoAbogadosPlaywrightAdapter()
        with pytest.raises(FuenteForoNoDisponibleError):
            adapter.buscar_por_persona_master(None)  # type: ignore
