"""Test: dos peticiones simultaneas -- Modulo 10, Submodulo 10.21.

"Dos peticiones POST /entidades/{id}/actualizar NO deben provocar doble
descarga/extraccion/SENESCYT/Foro innecesarios -- el Orchestrator sigue
siendo la autoridad." El bloqueo optimista REAL ya esta probado a fondo
en el Modulo 9 (`tests/integration/test_concurrencia_modulo9.py`, hilos +
SQLite real); aqui se prueba que la capa HTTP no agrega un segundo
mecanismo de lock propio -- cada peticion abre su PROPIA `Session` (via
`get_sesion`) y ambas terminan invocando al MISMO `GovDataPipelineOrchestrator`
(la unica autoridad), nunca un motor paralelo nuevo."""

from __future__ import annotations

import threading

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from govdata.application.dto.resultado_orquestacion_dto import ResultadoOrquestacionDTO
from govdata.infrastructure.api import dependencies as deps
from govdata.infrastructure.api.app import crear_app
from tests.integration.api.factories import crear_entidad


class _OrquestadorContadorLlamadas:
    """Doble compartido entre ambos hilos -- si la API introdujera un
    segundo mecanismo de concurrencia propio, este contador lo revelaria
    (cada peticion HTTP debe llamar exactamente UNA vez al Orchestrator)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.llamadas = 0

    def actualizar_entidad(self, nombre_entidad: str) -> ResultadoOrquestacionDTO:
        with self._lock:
            self.llamadas += 1
        return ResultadoOrquestacionDTO(
            job={"id": f"job-{self.llamadas}", "estado": "completado"},
            entidad={"nombre": nombre_entidad}, duracion_total="0.01s",
        )


def test_dos_actualizaciones_simultaneas_llaman_al_orchestrator_exactamente_una_vez_cada_una(
    sqlite_engine_multihilo,
) -> None:
    Factory = sessionmaker(bind=sqlite_engine_multihilo, future=True)
    sesion_setup = Factory()
    entidad = crear_entidad(sesion_setup, "Entidad Concurrente")
    sesion_setup.commit()
    sesion_setup.close()

    fake_orquestador = _OrquestadorContadorLlamadas()
    app = crear_app()

    def _get_sesion_override():
        sesion = Factory()
        try:
            yield sesion
            sesion.commit()
        finally:
            sesion.close()

    app.dependency_overrides[deps.get_sesion] = _get_sesion_override
    app.dependency_overrides[deps.get_orquestador] = lambda: fake_orquestador

    resultados: list[int] = []
    lock_resultados = threading.Lock()

    def _peticion() -> None:
        with TestClient(app) as client:
            respuesta = client.post(f"/api/v1/entidades/{entidad.id}/actualizar")
            with lock_resultados:
                resultados.append(respuesta.status_code)

    hilos = [threading.Thread(target=_peticion) for _ in range(2)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    assert resultados == [200, 200]
    assert fake_orquestador.llamadas == 2
