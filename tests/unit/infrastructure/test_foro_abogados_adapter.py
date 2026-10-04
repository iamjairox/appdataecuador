"""Tests para el adaptador del Foro de Abogados de la Función Judicial."""

from __future__ import annotations

import pytest

from govdata.infrastructure.scraping.playwright.foro_abogados_adapter import (
    ForoAbogadosPlaywrightAdapter,
    FuenteForoNoDisponibleError,
    SelectoresForoAbogados,
)
from govdata.infrastructure.scraping.playwright.selectors import foro_abogados_selectors


class TestSelectoresForoAbogados:
    """Tests para los selectores centralizados."""

    def test_selectores_por_defecto(self) -> None:
        selectores = SelectoresForoAbogados()
        assert selectores.input_cedula == "#CEDULA"
        assert selectores.boton_aceptar == "#btnValidarReg"
        assert selectores.campo_email == "#EMAIL"
        assert selectores.campo_celular == "#CELULAR"
        assert selectores.campo_nombres == "#NOMBRES"
        assert selectores.campo_apellidos == "#APELLIDOS"
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
        assert adapter._detectar_captcha("Just a moment") is True
        assert adapter._detectar_captcha("Checking your browser") is True
        assert adapter._detectar_captcha("formulario con recaptcha embebido") is False
        assert adapter._detectar_captcha("normal content") is False

    def test_detectar_confirmacion_de_registro_existente(self) -> None:
        adapter = ForoAbogadosPlaywrightAdapter()
        assert adapter._requiere_confirmacion_registro("La cédula ya se encuentra registrada") is True
        assert adapter._requiere_confirmacion_registro("No se encontraron datos") is False

    def test_buscar_por_persona_master_no_soportado(self) -> None:
        """El Foro de Abogados solo permite búsqueda por cédula, no por nombre."""
        adapter = ForoAbogadosPlaywrightAdapter()
        with pytest.raises(FuenteForoNoDisponibleError):
            adapter.buscar_por_persona_master(None)  # type: ignore
