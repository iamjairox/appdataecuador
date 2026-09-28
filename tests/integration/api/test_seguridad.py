"""Tests: seguridad -- Modulo 10 (API Key, CORS, rate limit, no exposicion
de secretos/stack traces)."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi.testclient import TestClient

from govdata.config.settings import ApiSettings
from govdata.infrastructure.api import dependencies as deps
from govdata.infrastructure.api.app import crear_app


def _cliente_con_settings(sesion, api_settings: ApiSettings) -> Iterator[TestClient]:
    app = crear_app(api_settings=api_settings)

    def _get_sesion_override():
        yield sesion

    def _get_api_settings_override() -> ApiSettings:
        return api_settings

    app.dependency_overrides[deps.get_sesion] = _get_sesion_override
    app.dependency_overrides[deps.get_api_settings] = _get_api_settings_override
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


class TestApiKey:
    def test_sin_api_key_configurada_no_exige_header(self, cliente) -> None:
        # `cliente` (conftest) usa la configuracion real de `development`
        # (`API_KEY=""`) -- la verificacion queda deshabilitada.
        assert cliente.get("/api/v1/entidades").status_code == 200

    def test_con_api_key_configurada_exige_header(self, sesion) -> None:
        settings = ApiSettings(API_KEY="secreto-123")
        for client in _cliente_con_settings(sesion, settings):
            respuesta = client.get("/api/v1/entidades")
            assert respuesta.status_code == 401
            assert respuesta.json()["error"]["codigo"] == "HTTP_401"

    def test_con_api_key_incorrecta_da_401(self, sesion) -> None:
        settings = ApiSettings(API_KEY="secreto-123")
        for client in _cliente_con_settings(sesion, settings):
            respuesta = client.get("/api/v1/entidades", headers={"X-API-Key": "otra-cosa"})
            assert respuesta.status_code == 401

    def test_con_api_key_correcta_pasa(self, sesion) -> None:
        settings = ApiSettings(API_KEY="secreto-123")
        for client in _cliente_con_settings(sesion, settings):
            respuesta = client.get("/api/v1/entidades", headers={"X-API-Key": "secreto-123"})
            assert respuesta.status_code == 200

    def test_sistema_nunca_exige_api_key(self, sesion) -> None:
        settings = ApiSettings(API_KEY="secreto-123")
        for client in _cliente_con_settings(sesion, settings):
            assert client.get("/health").status_code == 200


class TestCors:
    def test_responde_con_headers_cors_para_origen_permitido(self, cliente) -> None:
        respuesta = cliente.get("/api/v1/entidades", headers={"Origin": "https://cliente.test"})
        assert respuesta.headers.get("access-control-allow-origin") == "*"


class TestRateLimit:
    def test_excede_el_limite_configurado_da_429(self, sesion) -> None:
        settings = ApiSettings(RATE_LIMIT_POR_MINUTO=3)
        for client in _cliente_con_settings(sesion, settings):
            respuestas = [client.get("/api/v1/entidades") for _ in range(5)]
            codigos = [r.status_code for r in respuestas]
            assert codigos.count(429) >= 1
            ultima_429 = next(r for r in respuestas if r.status_code == 429)
            assert ultima_429.json()["error"]["codigo"] == "RATE_LIMIT_EXCEDIDO"


class TestNoExposicionDeSecretos:
    def test_error_inesperado_no_expone_stack_trace_ni_detalle_crudo(self, cliente, monkeypatch) -> None:
        from govdata.infrastructure.persistence.postgresql.repositories import (
            sqlalchemy_entidad_repository,
        )

        def _falla(self, entidad_id: int):
            raise RuntimeError("boom interno con password=supersecreto")

        monkeypatch.setattr(
            sqlalchemy_entidad_repository.SqlAlchemyEntidadRepository, "buscar_por_id", _falla,
        )

        respuesta = cliente.get("/api/v1/entidades/1")

        assert respuesta.status_code == 500
        cuerpo = respuesta.json()
        assert cuerpo["error"]["codigo"] == "ERROR_INTERNO"
        assert "supersecreto" not in respuesta.text
        assert "Traceback" not in respuesta.text
        assert "boom interno" not in respuesta.text
