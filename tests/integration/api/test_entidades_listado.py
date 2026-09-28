"""Tests: GET /entidades, GET /entidades/{id} -- Modulo 10."""

from __future__ import annotations

from tests.integration.api.factories import crear_entidad


class TestListarEntidades:
    def test_lista_vacia(self, cliente) -> None:
        respuesta = cliente.get("/api/v1/entidades")
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo == {"items": [], "page": 1, "page_size": 50, "total": 0, "pages": 0}

    def test_lista_entidades_persistidas(self, cliente, sesion) -> None:
        crear_entidad(sesion, "Entidad A")
        crear_entidad(sesion, "Entidad B")

        respuesta = cliente.get("/api/v1/entidades")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["total"] == 2
        assert {i["nombre"] for i in cuerpo["items"]} == {"Entidad A", "Entidad B"}
        assert cuerpo["items"][0]["portal_origen"] == "dpe"
        assert cuerpo["items"][0]["estado"] == "activa"

    def test_filtro_por_nombre(self, cliente, sesion) -> None:
        crear_entidad(sesion, "Procuraduria General del Estado")
        crear_entidad(sesion, "Ministerio de Salud")

        respuesta = cliente.get("/api/v1/entidades", params={"nombre": "Procuraduria"})

        cuerpo = respuesta.json()
        assert cuerpo["total"] == 1
        assert cuerpo["items"][0]["nombre"] == "Procuraduria General del Estado"

    def test_paginacion(self, cliente, sesion) -> None:
        for i in range(5):
            crear_entidad(sesion, f"Entidad {i}")

        respuesta = cliente.get("/api/v1/entidades", params={"page": 2, "page_size": 2})

        cuerpo = respuesta.json()
        assert cuerpo["page"] == 2
        assert cuerpo["page_size"] == 2
        assert cuerpo["total"] == 5
        assert cuerpo["pages"] == 3
        assert len(cuerpo["items"]) == 2

    def test_page_size_excede_el_maximo_configurado_da_422(self, cliente) -> None:
        respuesta = cliente.get("/api/v1/entidades", params={"page_size": 9999})
        assert respuesta.status_code == 422
        assert respuesta.json()["error"]["codigo"] == "HTTP_422"

    def test_page_menor_a_uno_da_422(self, cliente) -> None:
        respuesta = cliente.get("/api/v1/entidades", params={"page": 0})
        assert respuesta.status_code == 422


class TestObtenerEntidad:
    def test_detalle_existente(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}")

        assert respuesta.status_code == 200
        assert respuesta.json()["nombre"] == "Entidad X"

    def test_no_encontrada_da_404_con_contrato_de_error(self, cliente) -> None:
        respuesta = cliente.get("/api/v1/entidades/999999")

        assert respuesta.status_code == 404
        cuerpo = respuesta.json()
        assert cuerpo["error"]["codigo"] == "HTTP_404"
        assert "request_id" in cuerpo["error"]

    def test_respuesta_incluye_x_request_id(self, cliente) -> None:
        respuesta = cliente.get("/api/v1/entidades/999999")
        assert "X-Request-ID" in respuesta.headers
