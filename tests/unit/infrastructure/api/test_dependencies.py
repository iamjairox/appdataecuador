"""Tests: dependencies.py -- Modulo 10 (funciones puras de DI, sin HTTP)."""

from __future__ import annotations

from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from govdata.config.settings import ApiSettings
from govdata.infrastructure.api import dependencies as deps
from govdata.infrastructure.api.dependencies import ParametrosPaginacion, verificar_api_key


class TestVerificarApiKey:
    def test_sin_api_key_configurada_no_exige_nada(self) -> None:
        verificar_api_key(ApiSettings(API_KEY=""), x_api_key=None)  # no debe lanzar

    def test_con_api_key_configurada_y_header_ausente_lanza_401(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            verificar_api_key(ApiSettings(API_KEY="secreto"), x_api_key=None)
        assert exc_info.value.status_code == 401

    def test_con_api_key_incorrecta_lanza_401(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            verificar_api_key(ApiSettings(API_KEY="secreto"), x_api_key="otra")
        assert exc_info.value.status_code == 401

    def test_con_api_key_correcta_no_lanza(self) -> None:
        verificar_api_key(ApiSettings(API_KEY="secreto"), x_api_key="secreto")


class TestParametrosPaginacion:
    def test_page_size_dentro_del_limite(self) -> None:
        params = ParametrosPaginacion(ApiSettings(RATE_LIMIT_PAGINA_MAXIMA=100), page=1, page_size=50)
        assert params.page == 1
        assert params.page_size == 50

    def test_page_size_excede_el_maximo_lanza_422(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            ParametrosPaginacion(ApiSettings(RATE_LIMIT_PAGINA_MAXIMA=100), page=1, page_size=101)
        assert exc_info.value.status_code == 422

    def test_page_size_igual_al_maximo_no_lanza(self) -> None:
        params = ParametrosPaginacion(ApiSettings(RATE_LIMIT_PAGINA_MAXIMA=100), page=1, page_size=100)
        assert params.page_size == 100


class _ContainerFalso:
    """Doble minimo de `Container` -- solo lo que `get_sesion`/
    `get_orquestador` realmente tocan."""

    def __init__(self) -> None:
        self.sesion_entregada = object()
        self.orquestador_construido = object()

    @contextmanager
    def nueva_sesion(self):
        yield self.sesion_entregada

    def crear_govdata_pipeline_orchestrator(self, sesion):
        assert sesion is self.sesion_entregada
        return self.orquestador_construido


class TestGetSesion:
    def test_abre_y_cierra_una_sesion_via_container(self, monkeypatch) -> None:
        container_falso = _ContainerFalso()
        monkeypatch.setattr(deps, "get_container", lambda: container_falso)

        generador = deps.get_sesion()
        sesion = next(generador)
        assert sesion is container_falso.sesion_entregada

        with pytest.raises(StopIteration):
            next(generador)


class TestGetOrquestador:
    def test_construye_el_orquestador_via_container(self, monkeypatch) -> None:
        container_falso = _ContainerFalso()
        monkeypatch.setattr(deps, "get_container", lambda: container_falso)

        resultado = deps.get_orquestador(container_falso.sesion_entregada)

        assert resultado is container_falso.orquestador_construido
