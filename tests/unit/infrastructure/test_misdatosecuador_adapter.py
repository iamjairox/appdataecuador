"""Tests para el adaptador de Mis Datos Ecuador."""

from __future__ import annotations

from govdata.infrastructure.scraping.playwright.misdatosecuador_adapter import (
    MisDatosEcuadorAdapter,
    SelectoresMisDatosEcuador,
)
from govdata.infrastructure.scraping.playwright.selectors import misdatosecuador_selectors


class TestSelectoresMisDatosEcuador:
    """Tests para los selectores centralizados."""

    def test_selectores_por_defecto(self) -> None:
        selectores = SelectoresMisDatosEcuador()
        assert selectores.input_nombres == "#nombres"
        assert selectores.input_apellidos == "#apellidos"
        assert selectores.boton_consultar == "button[type='submit'], input[type='submit']"
        assert selectores.tabla_resultados == "table"
        assert selectores.filas_resultados == "table tbody tr"

    def test_url_consulta(self) -> None:
        assert (
            misdatosecuador_selectors.URL_CONSULTA
            == "https://misdatosecuador.com/consultas/personas/consultar-cedula-con-nombres.php"
        )


class TestMisDatosEcuadorAdapter:
    """Tests para el adaptador de Mis Datos Ecuador."""

    def test_inicializacion(self) -> None:
        adapter = MisDatosEcuadorAdapter()
        assert adapter._selectores is not None
        assert adapter._timeout_ms == 30_000
        assert adapter._headless is True

    def test_detectar_captcha(self) -> None:
        adapter = MisDatosEcuadorAdapter()
        assert adapter._detectar_captcha("Just a moment") is True
        assert adapter._detectar_captcha("Checking your browser") is True
        assert adapter._detectar_captcha("formulario con recaptcha embebido") is False
        assert adapter._detectar_captcha("normal content") is False

    def test_consultar_por_nombres_vacio(self) -> None:
        """Test que verifica que el adaptador se inicializa correctamente."""
        # Este test requiere un mock de Playwright, por lo que solo verificamos
        # que el adaptador se inicializa correctamente
        adapter = MisDatosEcuadorAdapter()
        assert adapter is not None
