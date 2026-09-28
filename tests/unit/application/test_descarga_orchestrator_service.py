"""Tests: DescargaOrchestratorService (concurrencia, resiliencia, metricas)."""

from __future__ import annotations

import pytest

from govdata.application.dto.resultado_descarga_dto import ResultadoDescargaDocumentoDTO
from govdata.application.ports.descarga_worker_port import DescargaWorkerPort
from govdata.application.services.descarga_orchestrator_service import DescargaOrchestratorService
from govdata.domain.entities.documento import DocumentoTransparencia, TipoArchivo


def _documento(n: int, tamano_bytes: int | None = None) -> DocumentoTransparencia:
    doc = DocumentoTransparencia(
        id=n,
        publicacion_id=n,
        tipo_archivo=TipoArchivo.PDF,
        nombre_original=f"doc-{n}.pdf",
        url_documento=f"https://x/{n}.pdf",
    )
    doc.tamano_bytes = tamano_bytes
    return doc


class _WorkerControlado(DescargaWorkerPort):
    instancias_creadas = 0
    cierres = 0

    def __init__(self, fallar_con: int | None = None, omitir_con: int | None = None) -> None:
        type(self).instancias_creadas += 1
        self._fallar_con = fallar_con
        self._omitir_con = omitir_con

    def procesar(self, documento: DocumentoTransparencia) -> ResultadoDescargaDocumentoDTO:
        if self._omitir_con == documento.id:
            return ResultadoDescargaDocumentoDTO(documento=documento, exito=False, omitido=True, error="omitido")
        if self._fallar_con == documento.id:
            return ResultadoDescargaDocumentoDTO(documento=documento, exito=False, error="fallo simulado")
        documento.tamano_bytes = 1000
        return ResultadoDescargaDocumentoDTO(documento=documento, exito=True)

    def cerrar(self) -> None:
        type(self).cierres += 1


@pytest.fixture(autouse=True)
def _reset_contadores():
    _WorkerControlado.instancias_creadas = 0
    _WorkerControlado.cierres = 0
    yield


def test_procesa_todos_los_documentos() -> None:
    servicio = DescargaOrchestratorService(worker_factory=_WorkerControlado, concurrencia_maxima=2)
    resumen = servicio.ejecutar([_documento(i) for i in range(5)])

    assert resumen.total_documentos == 5
    assert resumen.descargados == 5
    assert resumen.errores == 0


def test_un_fallo_no_detiene_el_resto() -> None:
    servicio = DescargaOrchestratorService(
        worker_factory=lambda: _WorkerControlado(fallar_con=2), concurrencia_maxima=2
    )
    resumen = servicio.ejecutar([_documento(i) for i in range(5)])

    assert resumen.total_documentos == 5
    assert resumen.errores == 1
    assert resumen.descargados == 4


def test_omitidos_no_cuentan_como_error() -> None:
    servicio = DescargaOrchestratorService(
        worker_factory=lambda: _WorkerControlado(omitir_con=1), concurrencia_maxima=2
    )
    resumen = servicio.ejecutar([_documento(i) for i in range(3)])

    assert resumen.omitidos == 1
    assert resumen.errores == 0
    assert resumen.descargados == 2


def test_excepcion_inesperada_no_detiene_el_pipeline() -> None:
    class _WorkerConBug(DescargaWorkerPort):
        def procesar(self, documento: DocumentoTransparencia) -> ResultadoDescargaDocumentoDTO:
            raise RuntimeError("bug inesperado")

        def cerrar(self) -> None:
            pass

    servicio = DescargaOrchestratorService(worker_factory=_WorkerConBug, concurrencia_maxima=2)
    resumen = servicio.ejecutar([_documento(i) for i in range(3)])

    assert resumen.total_documentos == 3
    assert resumen.errores == 3


def test_reutiliza_un_worker_por_hilo() -> None:
    servicio = DescargaOrchestratorService(worker_factory=_WorkerControlado, concurrencia_maxima=2)
    servicio.ejecutar([_documento(i) for i in range(10)])

    assert _WorkerControlado.instancias_creadas <= 2


def test_cierra_todos_los_workers_creados() -> None:
    servicio = DescargaOrchestratorService(worker_factory=_WorkerControlado, concurrencia_maxima=3)
    servicio.ejecutar([_documento(i) for i in range(6)])

    assert _WorkerControlado.cierres == _WorkerControlado.instancias_creadas
    assert _WorkerControlado.cierres > 0


def test_suma_bytes_totales_solo_de_exitosos() -> None:
    servicio = DescargaOrchestratorService(
        worker_factory=lambda: _WorkerControlado(fallar_con=1), concurrencia_maxima=1
    )
    resumen = servicio.ejecutar([_documento(1), _documento(2)])

    assert resumen.bytes_totales == 1000  # solo el documento 2 (exitoso)


def test_concurrencia_invalida_lanza_error() -> None:
    with pytest.raises(ValueError):
        DescargaOrchestratorService(worker_factory=_WorkerControlado, concurrencia_maxima=0)


def test_lista_vacia() -> None:
    servicio = DescargaOrchestratorService(worker_factory=_WorkerControlado, concurrencia_maxima=2)
    resumen = servicio.ejecutar([])

    assert resumen.total_documentos == 0
    assert resumen.velocidad_promedio_bytes_por_segundo == 0
