"""Tests: HttpVerificadorCambiosAdapter -- Submodulo 5.15, chequeo HTTP
HEAD liviano. Fail-safe: cualquier ambiguedad responde `True` (hay que
descargar), nunca se omite una descarga real por error de este chequeo."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests

from govdata.infrastructure.http.http_verificador_cambios_adapter import (
    HttpVerificadorCambiosAdapter,
)


def _respuesta(status_code: int = 200, headers: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    return resp


class TestSinValoresPrevios:
    def test_sin_etag_ni_last_modified_conocidos_siempre_hay_cambios(self) -> None:
        adaptador = HttpVerificadorCambiosAdapter()
        assert adaptador.hay_cambios("https://x/d.pdf", None, None) is True


class TestComparacionPorEtag:
    def test_mismo_etag_no_hay_cambios(self) -> None:
        adaptador = HttpVerificadorCambiosAdapter()
        with patch.object(adaptador._sesion, "head", return_value=_respuesta(headers={"ETag": "abc"})):
            assert adaptador.hay_cambios("https://x/d.pdf", "abc", None) is False

    def test_etag_distinto_hay_cambios(self) -> None:
        adaptador = HttpVerificadorCambiosAdapter()
        with patch.object(adaptador._sesion, "head", return_value=_respuesta(headers={"ETag": "nuevo"})):
            assert adaptador.hay_cambios("https://x/d.pdf", "viejo", None) is True


class TestComparacionPorLastModified:
    def test_mismo_last_modified_no_hay_cambios(self) -> None:
        adaptador = HttpVerificadorCambiosAdapter()
        with patch.object(adaptador._sesion, "head", return_value=_respuesta(headers={"Last-Modified": "Mon, 01 Jun 2026"})):
            assert adaptador.hay_cambios("https://x/d.pdf", None, "Mon, 01 Jun 2026") is False

    def test_last_modified_distinto_hay_cambios(self) -> None:
        adaptador = HttpVerificadorCambiosAdapter()
        with patch.object(adaptador._sesion, "head", return_value=_respuesta(headers={"Last-Modified": "Tue, 01 Jul 2026"})):
            assert adaptador.hay_cambios("https://x/d.pdf", None, "Mon, 01 Jun 2026") is True


class TestFailSafe:
    def test_timeout_responde_hay_cambios(self) -> None:
        adaptador = HttpVerificadorCambiosAdapter()
        with patch.object(adaptador._sesion, "head", side_effect=requests.Timeout("timeout")):
            assert adaptador.hay_cambios("https://x/d.pdf", "abc", None) is True

    def test_status_error_responde_hay_cambios(self) -> None:
        adaptador = HttpVerificadorCambiosAdapter()
        with patch.object(adaptador._sesion, "head", return_value=_respuesta(status_code=500)):
            assert adaptador.hay_cambios("https://x/d.pdf", "abc", None) is True

    def test_servidor_sin_condicionales_comparables_responde_hay_cambios(self) -> None:
        adaptador = HttpVerificadorCambiosAdapter()
        with patch.object(adaptador._sesion, "head", return_value=_respuesta(headers={})):
            assert adaptador.hay_cambios("https://x/d.pdf", "abc", None) is True


def test_cerrar_cierra_la_sesion() -> None:
    adaptador = HttpVerificadorCambiosAdapter()
    with patch.object(adaptador._sesion, "close") as mock_close:
        adaptador.cerrar()
        mock_close.assert_called_once()
