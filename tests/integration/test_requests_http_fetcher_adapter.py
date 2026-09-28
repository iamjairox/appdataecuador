"""Tests de integracion: RequestsHttpFetcherAdapter contra un servidor
HTTP local real (200/404/500/timeout/pagina-de-error/corrupto)."""

from __future__ import annotations

import pytest

from govdata.domain.exceptions.domain_exceptions import (
    ContenidoInvalidoError,
    DescargaFallidaError,
    RecursoNoDisponibleError,
)
from govdata.infrastructure.http.requests_http_fetcher_adapter import RequestsHttpFetcherAdapter


@pytest.fixture()
def adapter(servidor_fixtures_descarga):
    adaptador = RequestsHttpFetcherAdapter(
        timeout_segundos=1.0, max_reintentos=2, backoff_base_segundos=0.05
    )
    yield adaptador
    adaptador.cerrar()


class TestDescargaExitosa:
    def test_descarga_pdf_con_headers(self, adapter, servidor_fixtures_descarga) -> None:
        respuesta = adapter.descargar(f"{servidor_fixtures_descarga.url_origen}/archivo/valido.pdf")

        assert respuesta.codigo_http == 200
        assert respuesta.contenido.startswith(b"%PDF-")
        assert respuesta.content_type == "application/pdf"
        assert respuesta.etag == '"etag-de-prueba"'
        assert respuesta.last_modified == "Tue, 04 Aug 2026 10:00:00 GMT"

    def test_descarga_xlsx(self, adapter, servidor_fixtures_descarga) -> None:
        respuesta = adapter.descargar(f"{servidor_fixtures_descarga.url_origen}/archivo/valido.xlsx")
        assert respuesta.contenido.startswith(b"PK\x03\x04")

    def test_descarga_vacia(self, adapter, servidor_fixtures_descarga) -> None:
        respuesta = adapter.descargar(f"{servidor_fixtures_descarga.url_origen}/archivo/vacio")
        assert respuesta.contenido == b""


class TestErroresHttp:
    def test_404_lanza_recurso_no_disponible(self, adapter, servidor_fixtures_descarga) -> None:
        with pytest.raises(RecursoNoDisponibleError):
            adapter.descargar(f"{servidor_fixtures_descarga.url_origen}/archivo/no-encontrado")

    def test_500_lanza_descarga_fallida(self, servidor_fixtures_descarga) -> None:
        # max_reintentos=1: falla rapido, sin esperar el backoff completo.
        adaptador = RequestsHttpFetcherAdapter(
            timeout_segundos=1.0, max_reintentos=1, backoff_base_segundos=0.01
        )
        try:
            with pytest.raises(DescargaFallidaError):
                adaptador.descargar(f"{servidor_fixtures_descarga.url_origen}/archivo/error-servidor")
        finally:
            adaptador.cerrar()

    def test_timeout_lanza_descarga_fallida(self, servidor_fixtures_descarga) -> None:
        servidor_fixtures_descarga.segundos_de_retraso = 2.0
        adaptador = RequestsHttpFetcherAdapter(
            timeout_segundos=0.3, max_reintentos=1, backoff_base_segundos=0.01
        )
        try:
            with pytest.raises(DescargaFallidaError, match="Timeout"):
                adaptador.descargar(f"{servidor_fixtures_descarga.url_origen}/archivo/lento")
        finally:
            adaptador.cerrar()


class TestReintentos:
    def test_recupera_tras_fallos_transitorios(self, adapter, servidor_fixtures_descarga) -> None:
        servidor_fixtures_descarga.intentos_fallidos_restantes = 1
        respuesta = adapter.descargar(f"{servidor_fixtures_descarga.url_origen}/archivo/flaky")
        assert respuesta.codigo_http == 200

    def test_agota_reintentos_y_propaga(self, servidor_fixtures_descarga) -> None:
        servidor_fixtures_descarga.intentos_fallidos_restantes = 10
        adaptador = RequestsHttpFetcherAdapter(
            timeout_segundos=1.0, max_reintentos=2, backoff_base_segundos=0.01
        )
        try:
            with pytest.raises(DescargaFallidaError):
                adaptador.descargar(f"{servidor_fixtures_descarga.url_origen}/archivo/flaky")
        finally:
            adaptador.cerrar()


class TestLimiteDeTamano:
    def test_corta_si_excede_tamano_maximo(self, servidor_fixtures_descarga) -> None:
        adaptador = RequestsHttpFetcherAdapter(
            timeout_segundos=1.0, max_reintentos=1, backoff_base_segundos=0.01, tamano_maximo_bytes=10
        )
        try:
            with pytest.raises(ContenidoInvalidoError):
                adaptador.descargar(f"{servidor_fixtures_descarga.url_origen}/archivo/valido.pdf")
        finally:
            adaptador.cerrar()
