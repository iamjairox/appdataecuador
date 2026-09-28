"""Tests: politica de reintentos compartida."""

from __future__ import annotations

import pytest

from govdata.domain.exceptions.domain_exceptions import (
    DescargaFallidaError,
    DocumentoNoSoportadoError,
)
from govdata.shared.retry.retry_policy import con_reintentos, es_error_permanente


def test_reintenta_hasta_tener_exito() -> None:
    intentos = {"contador": 0}

    @con_reintentos(max_intentos=3, espera_inicial_segundos=0.01, espera_maxima_segundos=0.02)
    def operacion_inestable() -> str:
        intentos["contador"] += 1
        if intentos["contador"] < 3:
            raise DescargaFallidaError("fallo transitorio")
        return "ok"

    assert operacion_inestable() == "ok"
    assert intentos["contador"] == 3


def test_agota_intentos_y_relanza() -> None:
    @con_reintentos(max_intentos=2, espera_inicial_segundos=0.01, espera_maxima_segundos=0.02)
    def siempre_falla() -> None:
        raise DescargaFallidaError("nunca se recupera")

    with pytest.raises(DescargaFallidaError):
        siempre_falla()


def test_no_reintenta_errores_no_configurados() -> None:
    """Un error no incluido en `errores_reintentables` se propaga en el
    primer intento (ej. errores permanentes de negocio)."""
    intentos = {"contador": 0}

    @con_reintentos(max_intentos=5, espera_inicial_segundos=0.01, espera_maxima_segundos=0.02)
    def falla_permanente() -> None:
        intentos["contador"] += 1
        raise DocumentoNoSoportadoError("formato desconocido")

    with pytest.raises(DocumentoNoSoportadoError):
        falla_permanente()
    assert intentos["contador"] == 1


def test_es_error_permanente() -> None:
    assert es_error_permanente(DocumentoNoSoportadoError("x")) is True
    assert es_error_permanente(DescargaFallidaError("x")) is False
