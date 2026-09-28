"""Tests: PipelineOrchestratorService (concurrencia, resiliencia, metricas)."""

from __future__ import annotations

import threading

import pytest

from govdata.application.dto.resultado_descubrimiento_dto import ResultadoDescubrimientoEntidadDTO
from govdata.application.ports.entidad_worker_port import EntidadWorkerPort
from govdata.application.services.pipeline_orchestrator_service import PipelineOrchestratorService
from govdata.domain.entities.entidad import Entidad


def _entidad(n: int) -> Entidad:
    return Entidad(id=n, nombre=f"Entidad {n}", url_transparencia=f"https://x/{n}", portal_origen="dpe")


class _WorkerControlado(EntidadWorkerPort):
    """Worker fake: cuenta cuantas instancias se crean (para verificar
    reutilizacion por hilo) y cuantas veces se cierra."""

    instancias_creadas = 0
    cierres = 0

    def __init__(self, fallar_con: str | None = None, lanzar_excepcion: bool = False) -> None:
        type(self).instancias_creadas += 1
        self._fallar_con = fallar_con
        self._lanzar_excepcion = lanzar_excepcion
        self.hilo_usado: set[int] = set()

    def procesar(self, entidad: Entidad) -> ResultadoDescubrimientoEntidadDTO:
        self.hilo_usado.add(threading.get_ident())
        if self._lanzar_excepcion:
            raise RuntimeError("bug inesperado en el worker")
        if self._fallar_con and entidad.nombre == self._fallar_con:
            return ResultadoDescubrimientoEntidadDTO(
                entidad=entidad, publicacion=None, documento=None, exito=False, error="fallo simulado"
            )
        return ResultadoDescubrimientoEntidadDTO(
            entidad=entidad, publicacion=None, documento=None, exito=True, error=None
        )

    def cerrar(self) -> None:
        type(self).cierres += 1


@pytest.fixture(autouse=True)
def _reset_contadores():
    _WorkerControlado.instancias_creadas = 0
    _WorkerControlado.cierres = 0
    yield


def test_procesa_todas_las_entidades() -> None:
    servicio = PipelineOrchestratorService(worker_factory=_WorkerControlado, concurrencia_maxima=2)
    entidades = [_entidad(i) for i in range(5)]

    resumen = servicio.ejecutar(entidades)

    assert resumen.total_entidades == 5
    assert resumen.errores == 0


def test_un_fallo_no_detiene_el_resto() -> None:
    servicio = PipelineOrchestratorService(
        worker_factory=lambda: _WorkerControlado(fallar_con="Entidad 2"), concurrencia_maxima=2
    )
    entidades = [_entidad(i) for i in range(5)]

    resumen = servicio.ejecutar(entidades)

    assert resumen.total_entidades == 5
    assert resumen.errores == 1


def test_excepcion_inesperada_en_worker_no_detiene_el_pipeline() -> None:
    """Ultima linea de defensa: incluso un bug (RuntimeError) en un worker
    no debe tumbar el pipeline completo."""
    servicio = PipelineOrchestratorService(
        worker_factory=lambda: _WorkerControlado(lanzar_excepcion=True), concurrencia_maxima=2
    )
    entidades = [_entidad(i) for i in range(3)]

    resumen = servicio.ejecutar(entidades)

    assert resumen.total_entidades == 3
    assert resumen.errores == 3


def test_reutiliza_un_worker_por_hilo_no_por_entidad() -> None:
    """Con concurrencia=2 y 10 entidades, deben crearse a lo sumo 2 workers
    (uno por hilo), nunca 10."""
    servicio = PipelineOrchestratorService(worker_factory=_WorkerControlado, concurrencia_maxima=2)
    entidades = [_entidad(i) for i in range(10)]

    servicio.ejecutar(entidades)

    assert _WorkerControlado.instancias_creadas <= 2


def test_cierra_todos_los_workers_creados() -> None:
    servicio = PipelineOrchestratorService(worker_factory=_WorkerControlado, concurrencia_maxima=3)
    servicio.ejecutar([_entidad(i) for i in range(6)])

    assert _WorkerControlado.cierres == _WorkerControlado.instancias_creadas
    assert _WorkerControlado.cierres > 0


def test_registra_duracion_positiva() -> None:
    servicio = PipelineOrchestratorService(worker_factory=_WorkerControlado, concurrencia_maxima=1)
    resumen = servicio.ejecutar([_entidad(1)])

    assert resumen.duracion_segundos >= 0


def test_concurrencia_invalida_lanza_error() -> None:
    with pytest.raises(ValueError):
        PipelineOrchestratorService(worker_factory=_WorkerControlado, concurrencia_maxima=0)


def test_lista_vacia_retorna_resumen_en_cero() -> None:
    servicio = PipelineOrchestratorService(worker_factory=_WorkerControlado, concurrencia_maxima=2)
    resumen = servicio.ejecutar([])

    assert resumen.total_entidades == 0
    assert resumen.errores == 0
