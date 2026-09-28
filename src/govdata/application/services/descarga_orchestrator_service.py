"""Servicio: DescargaOrchestratorService.

Reparte la descarga de un lote de documentos entre N workers, en
paralelo, garantizando que un fallo (incluso inesperado) en un documento
jamas detiene el procesamiento de los demas -- mismo principio que
`PipelineOrchestratorService` del Modulo 2.

Nota de diseno: aqui SI se usa el mismo patron de pool de hilos manual
(`queue.Queue` + `threading.Thread`, cada hilo crea y cierra su propio
worker) que en el Modulo 2, aunque la razon es distinta: no es Playwright
(no aplica aqui), sino que tanto una `requests.Session` como una
`sqlalchemy.orm.Session` estan documentadas como NO seguras para
compartir entre hilos -- el patron "un worker (con sus propios recursos)
por hilo, reutilizado entre los documentos que le toquen" sigue siendo la
forma correcta de lograr concurrencia real sin arriesgar corrupcion de
estado compartido.
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from datetime import UTC, datetime

from govdata.application.dto.resultado_descarga_dto import ResultadoDescargaDocumentoDTO
from govdata.application.dto.resumen_descarga_dto import ResumenDescargaDTO
from govdata.application.ports.descarga_worker_port import DescargaWorkerPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import DocumentoTransparencia

logger = get_logger(__name__)

_SENTINEL_FIN_DE_COLA = None


class DescargaOrchestratorService:
    """Reparte la descarga de un lote de documentos entre N workers."""

    def __init__(
        self,
        worker_factory: Callable[[], DescargaWorkerPort],
        concurrencia_maxima: int = 4,
    ) -> None:
        if concurrencia_maxima < 1:
            raise ValueError("concurrencia_maxima debe ser >= 1")
        self._worker_factory = worker_factory
        self._concurrencia_maxima = concurrencia_maxima

    def ejecutar(self, documentos: list[DocumentoTransparencia]) -> ResumenDescargaDTO:
        iniciado_en = datetime.now(UTC)
        logger.info(
            "descarga_pipeline_iniciado",
            total_documentos=len(documentos),
            concurrencia_maxima=self._concurrencia_maxima,
        )

        resultados = self._procesar_en_paralelo(documentos)

        finalizado_en = datetime.now(UTC)
        resumen = self._construir_resumen(documentos, resultados, iniciado_en, finalizado_en)

        logger.info(
            "descarga_pipeline_finalizado",
            total_documentos=resumen.total_documentos,
            descargados=resumen.descargados,
            omitidos=resumen.omitidos,
            errores=resumen.errores,
            bytes_totales=resumen.bytes_totales,
            duracion_segundos=round(resumen.duracion_segundos, 3),
            velocidad_promedio_bytes_por_segundo=round(resumen.velocidad_promedio_bytes_por_segundo, 2),
        )
        return resumen

    def _procesar_en_paralelo(
        self, documentos: list[DocumentoTransparencia]
    ) -> list[ResultadoDescargaDocumentoDTO]:
        if not documentos:
            return []

        cola_trabajo: queue.Queue[DocumentoTransparencia | None] = queue.Queue()
        for documento in documentos:
            cola_trabajo.put(documento)

        cantidad_hilos = min(self._concurrencia_maxima, len(documentos))
        for _ in range(cantidad_hilos):
            cola_trabajo.put(_SENTINEL_FIN_DE_COLA)

        resultados: list[ResultadoDescargaDocumentoDTO] = []
        lock_resultados = threading.Lock()

        def _ejecutar_hilo_worker() -> None:
            worker: DescargaWorkerPort | None = None
            try:
                while True:
                    documento = cola_trabajo.get()
                    if documento is _SENTINEL_FIN_DE_COLA:
                        return
                    if worker is None:
                        worker = self._worker_factory()
                    resultado = self._procesar_con_defensa(worker, documento)
                    with lock_resultados:
                        resultados.append(resultado)
            finally:
                if worker is not None:
                    worker.cerrar()

        hilos = [
            threading.Thread(target=_ejecutar_hilo_worker, name=f"descarga-worker-{i}", daemon=True)
            for i in range(cantidad_hilos)
        ]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()

        return resultados

    @staticmethod
    def _procesar_con_defensa(
        worker: DescargaWorkerPort, documento: DocumentoTransparencia
    ) -> ResultadoDescargaDocumentoDTO:
        try:
            return worker.procesar(documento)
        except Exception as exc:  # noqa: BLE001 - ultima linea de defensa
            logger.error(
                "error_inesperado_descargando_documento", documento_id=documento.id, error=str(exc)
            )
            return ResultadoDescargaDocumentoDTO(documento=documento, exito=False, error=f"error inesperado: {exc}")

    @staticmethod
    def _construir_resumen(
        documentos: list[DocumentoTransparencia],
        resultados: list[ResultadoDescargaDocumentoDTO],
        iniciado_en: datetime,
        finalizado_en: datetime,
    ) -> ResumenDescargaDTO:
        descargados = [r for r in resultados if r.exito]
        omitidos = sum(1 for r in resultados if r.omitido)
        errores = sum(1 for r in resultados if not r.exito and not r.omitido)
        bytes_totales = sum(r.documento.tamano_bytes or 0 for r in descargados)
        return ResumenDescargaDTO(
            total_documentos=len(documentos),
            descargados=len(descargados),
            omitidos=omitidos,
            errores=errores,
            bytes_totales=bytes_totales,
            iniciado_en=iniciado_en,
            finalizado_en=finalizado_en,
        )
