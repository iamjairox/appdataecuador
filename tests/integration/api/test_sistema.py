"""Tests: rutas de Sistema -- Modulo 10 (health/ready/bienvenida/OpenAPI)."""

from __future__ import annotations


class TestHealth:
    def test_health_no_toca_la_base_de_datos(self, cliente) -> None:
        respuesta = cliente.get("/health")
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["status"] == "ok"
        assert cuerpo["service"] == "govdata-api"
        assert "version" in cuerpo
        assert "timestamp" in cuerpo


class TestReady:
    def test_ready_verifica_conexion_real_a_la_bd(self, cliente) -> None:
        respuesta = cliente.get("/ready")
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["checks"]["base_de_datos"] == "ok"
        assert cuerpo["checks"]["configuracion"] == "ok"


class TestBienvenida:
    def test_pagina_raiz(self, cliente) -> None:
        respuesta = cliente.get("/")
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["nombre"] == "GovData Intelligence Platform"
        assert cuerpo["documentacion"]["swagger"] == "/docs"


class TestOpenApi:
    def test_swagger_disponible(self, cliente) -> None:
        assert cliente.get("/docs").status_code == 200

    def test_redoc_disponible(self, cliente) -> None:
        assert cliente.get("/redoc").status_code == 200

    def test_openapi_json_incluye_los_tags_esperados(self, cliente) -> None:
        respuesta = cliente.get("/openapi.json")
        assert respuesta.status_code == 200
        esquema = respuesta.json()
        nombres_tags = {t["name"] for t in esquema["tags"]}
        assert {"Sistema", "Entidades", "Funcionarios", "Jobs"} <= nombres_tags
        assert "/api/v1/entidades/{entidad_id}/consulta" in esquema["paths"]
