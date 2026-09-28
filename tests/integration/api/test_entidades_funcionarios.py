"""Tests: GET /entidades/{id}/funcionarios y /funcionarios/exportar -- Modulo 10."""

from __future__ import annotations

import csv
import io
import json

from tests.integration.api.factories import crear_entidad, crear_funcionario_juridico_completo


class TestListarFuncionariosDeEntidad:
    def test_lista_funcionarios_persistidos(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        crear_funcionario_juridico_completo(sesion, entidad, cedula="0000000001")
        crear_funcionario_juridico_completo(sesion, entidad, nombres="Sara", apellidos="Perez", cedula="0000000002")

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/funcionarios")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["total"] == 2
        assert {i["cedula"] for i in cuerpo["items"]} == {"0000000001", "0000000002"}
        assert all(i["persona_master_id"] is not None for i in cuerpo["items"])

    def test_filtro_por_cedula(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        crear_funcionario_juridico_completo(sesion, entidad, cedula="0000000001")
        crear_funcionario_juridico_completo(sesion, entidad, nombres="Sara", apellidos="Perez", cedula="0000000002")

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/funcionarios", params={"cedula": "0000000002"})

        cuerpo = respuesta.json()
        assert cuerpo["total"] == 1
        assert cuerpo["items"][0]["cedula"] == "0000000002"

    def test_entidad_no_encontrada_da_404(self, cliente) -> None:
        respuesta = cliente.get("/api/v1/entidades/999999/funcionarios")
        assert respuesta.status_code == 404

    def test_filtro_por_nombre(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        crear_funcionario_juridico_completo(sesion, entidad, nombres="Ana", cedula="0000000001")
        crear_funcionario_juridico_completo(sesion, entidad, nombres="Sara", cedula="0000000002")

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/funcionarios", params={"nombre": "Ana"})

        assert respuesta.json()["total"] == 1

    def test_filtro_por_apellido(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        crear_funcionario_juridico_completo(sesion, entidad, apellidos="Torres", cedula="0000000001")
        crear_funcionario_juridico_completo(sesion, entidad, apellidos="Perez", cedula="0000000002")

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/funcionarios", params={"apellido": "Torres"})

        assert respuesta.json()["total"] == 1

    def test_filtro_por_cargo_y_dependencia(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        crear_funcionario_juridico_completo(sesion, entidad, cedula="0000000001")

        assert cliente.get(
            f"/api/v1/entidades/{entidad.id}/funcionarios", params={"cargo": "Procurador"},
        ).json()["total"] == 1
        assert cliente.get(
            f"/api/v1/entidades/{entidad.id}/funcionarios", params={"dependencia": "Direccion Juridica"},
        ).json()["total"] == 1
        assert cliente.get(
            f"/api/v1/entidades/{entidad.id}/funcionarios", params={"cargo": "No Existe"},
        ).json()["total"] == 0

    def test_filtro_por_area(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        crear_funcionario_juridico_completo(sesion, entidad, cedula="0000000001")

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/funcionarios", params={"area": "juridica"})

        assert respuesta.json()["total"] == 1

    def test_filtro_por_correo_y_telefono_no_coinciden_da_cero(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        crear_funcionario_juridico_completo(sesion, entidad, cedula="0000000001")

        assert cliente.get(
            f"/api/v1/entidades/{entidad.id}/funcionarios", params={"correo": "nadie@x.test"},
        ).json()["total"] == 0
        assert cliente.get(
            f"/api/v1/entidades/{entidad.id}/funcionarios", params={"telefono": "0999999999"},
        ).json()["total"] == 0

    def test_no_dispara_procesos_externos_solo_lee_bd(self, cliente, sesion) -> None:
        """No hay Orchestrator/SENESCYT/Foro involucrados -- si el endpoint
        intentara dispararlos, este test fallaria por falta de wiring de
        red/Playwright (ninguno esta disponible en esta suite)."""
        entidad = crear_entidad(sesion, "Entidad X")
        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/funcionarios")
        assert respuesta.status_code == 200


class TestExportarFuncionarios:
    def test_exportar_csv(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        crear_funcionario_juridico_completo(sesion, entidad, cedula="0000000001")

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/funcionarios/exportar", params={"formato": "csv"})

        assert respuesta.status_code == 200
        assert respuesta.headers["content-type"].startswith("text/csv")
        filas = list(csv.DictReader(io.StringIO(respuesta.text)))
        assert len(filas) == 1
        assert filas[0]["cedula"] == "0000000001"

    def test_exportar_json(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        crear_funcionario_juridico_completo(sesion, entidad, cedula="0000000001")

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/funcionarios/exportar", params={"formato": "json"})

        assert respuesta.status_code == 200
        datos = json.loads(respuesta.text)
        assert len(datos) == 1
        assert datos[0]["cedula"] == "0000000001"

    def test_exportar_sin_funcionarios_produce_solo_encabezado(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad Vacia")

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/funcionarios/exportar", params={"formato": "csv"})

        assert respuesta.status_code == 200
        assert list(csv.DictReader(io.StringIO(respuesta.text))) == []

    def test_formato_invalido_da_422(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/funcionarios/exportar", params={"formato": "xml"})
        assert respuesta.status_code == 422
