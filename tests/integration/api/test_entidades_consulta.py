"""Tests: /entidades/{id}/consulta, /actualizar, /consulta-masiva,
/actualizar-masivo -- Modulo 10.

Reglas de arquitectura probadas aqui (Submodulo 10.28): estos endpoints
SOLO llaman a `GovDataPipelineOrchestrator` (via `Depends(get_orquestador)`,
sobreescrito aqui con un doble) -- nunca reimplementan el pipeline. La
correccion del propio Orquestador (cache/monitoreo/bloqueo optimista) ya
esta probada en el Modulo 9; aqui se prueba el CONTRATO HTTP (que politica
se pasa, que forma tiene la respuesta, que un 404 de entidad nunca llega a
invocar el Orquestador)."""

from __future__ import annotations

from govdata.application.dto.resultado_orquestacion_dto import ResultadoOrquestacionDTO
from govdata.infrastructure.api import dependencies as deps
from tests.integration.api.factories import crear_entidad


class _OrquestadorFalso:
    def __init__(self) -> None:
        self.llamadas: list[tuple[str, ...]] = []

    def consultar_entidad(self, nombre_entidad: str, politica: str | None = None, pasos=None) -> ResultadoOrquestacionDTO:
        self.llamadas.append(("consultar_entidad", nombre_entidad, politica or ""))
        return ResultadoOrquestacionDTO(
            job={"id": "job-1", "estado": "completado", "politica": politica},
            entidad={"id": 1, "nombre": nombre_entidad},
            estadisticas={"funcionarios_juridicos": 1},
            funcionarios=[{"nombre_completo": "Ana Torres"}],
            duracion_total="0.01s",
        )

    def actualizar_entidad(self, nombre_entidad: str) -> ResultadoOrquestacionDTO:
        self.llamadas.append(("actualizar_entidad", nombre_entidad))
        return ResultadoOrquestacionDTO(
            job={"id": "job-2", "estado": "completado", "politica": "actualizacion_completa"},
            entidad={"id": 1, "nombre": nombre_entidad}, duracion_total="0.02s",
        )

    def consultar_masivo(self, politica: str | None = None) -> list[ResultadoOrquestacionDTO]:
        self.llamadas.append(("consultar_masivo", politica or ""))
        return [ResultadoOrquestacionDTO(job={"id": "job-3", "estado": "completado"}, entidad={"nombre": "Entidad A"}, duracion_total="0.01s")]

    def actualizar_masivo(self) -> list[ResultadoOrquestacionDTO]:
        self.llamadas.append(("actualizar_masivo",))
        return [ResultadoOrquestacionDTO(job={"id": "job-4", "estado": "completado"}, entidad={"nombre": "Entidad A"}, duracion_total="0.01s")]


def _sobreescribir_orquestador(cliente, fake: _OrquestadorFalso) -> None:
    cliente.app.dependency_overrides[deps.get_orquestador] = lambda: fake


class TestConsultarEntidad:
    def test_usa_el_orquestador_con_la_politica_por_defecto(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Procuraduria")
        fake = _OrquestadorFalso()
        _sobreescribir_orquestador(cliente, fake)

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/consulta")

        assert respuesta.status_code == 200
        assert fake.llamadas == [("consultar_entidad", "Procuraduria", "consulta_rapida")]
        cuerpo = respuesta.json()
        assert set(cuerpo) == {"job", "entidad", "estadisticas", "funcionarios", "alertas", "errores", "duracion_total", "generado_en"}

    def test_permite_elegir_politica(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Procuraduria")
        fake = _OrquestadorFalso()
        _sobreescribir_orquestador(cliente, fake)

        cliente.get(f"/api/v1/entidades/{entidad.id}/consulta", params={"politica": "solo_cambios"})

        assert fake.llamadas == [("consultar_entidad", "Procuraduria", "solo_cambios")]

    def test_entidad_no_encontrada_nunca_invoca_al_orquestador(self, cliente) -> None:
        fake = _OrquestadorFalso()
        _sobreescribir_orquestador(cliente, fake)

        respuesta = cliente.get("/api/v1/entidades/999999/consulta")

        assert respuesta.status_code == 404
        assert fake.llamadas == []


class TestActualizarEntidad:
    def test_fuerza_actualizacion_completa(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Procuraduria")
        fake = _OrquestadorFalso()
        _sobreescribir_orquestador(cliente, fake)

        respuesta = cliente.post(f"/api/v1/entidades/{entidad.id}/actualizar")

        assert respuesta.status_code == 200
        assert fake.llamadas == [("actualizar_entidad", "Procuraduria")]
        assert respuesta.json()["job"]["politica"] == "actualizacion_completa"


class TestConsultaYActualizacionMasiva:
    def test_consulta_masiva(self, cliente) -> None:
        fake = _OrquestadorFalso()
        _sobreescribir_orquestador(cliente, fake)

        respuesta = cliente.post("/api/v1/entidades/consulta-masiva")

        assert respuesta.status_code == 200
        assert len(respuesta.json()) == 1
        assert fake.llamadas == [("consultar_masivo", "consulta_rapida")]

    def test_actualizar_masivo(self, cliente) -> None:
        fake = _OrquestadorFalso()
        _sobreescribir_orquestador(cliente, fake)

        respuesta = cliente.post("/api/v1/entidades/actualizar-masivo")

        assert respuesta.status_code == 200
        assert fake.llamadas == [("actualizar_masivo",)]
