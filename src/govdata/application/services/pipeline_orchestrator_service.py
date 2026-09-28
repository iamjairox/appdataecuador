"""Servicio: PipelineOrchestratorService.

Orquesta el descubrimiento de publicacion+documento para un lote de
entidades, en paralelo, respetando `concurrencia_maxima`, y garantizando
que un fallo (incluso inesperado) en una entidad jamas detiene el
procesamiento de las demas.

Notas de diseno (documentadas explicitamente):

1. La concurrencia se implementa con hilos de la libreria estandar
   (`threading`), no con `concurrent.futures.ThreadPoolExecutor`. Es una
   excepcion deliberada y acotada a la regla "application no importa
   infraestructura": el mecanismo de hilos es un detalle de ejecucion:
   Playwright, la libreria que hace el trabajo real, no aparece aqui.

2. Por que NO se uso `ThreadPoolExecutor`: se verifico empiricamente que
   Playwright (Sync API) exige que un `Browser`/`BrowserContext` se cierre
   desde el MISMO hilo del sistema operativo que lo creo -- cerrarlo desde
   otro hilo lanza `greenlet.error: cannot switch to a different thread`.
   `ThreadPoolExecutor` no ofrece un hook para ejecutar codigo justo antes
   de que reutilice o destruya cada hilo de su pool, lo que hace imposible
   garantizar "cada worker se cierra en su propio hilo" de forma
   confiable. Por eso se implementa un pool de hilos simple con
   `queue.Queue`: cada hilo crea su worker perezosamente, procesa
   entidades hasta agotar la cola, y lo cierra el MISMO antes de terminar.
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from datetime import UTC, datetime

from govdata.application.dto.resultado_descubrimiento_dto import ResultadoDescubrimientoEntidadDTO
from govdata.application.dto.resumen_ejecucion_dto import ResumenEjecucionPipelineDTO
from govdata.application.ports.entidad_worker_port import EntidadWorkerPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.entidad import Entidad

logger = get_logger(__name__)

_SENTINEL_FIN_DE_COLA = None


class PipelineOrchestratorService:
    """Reparte el descubrimiento de un lote de entidades entre N workers."""

    def __init__(
        self,
        worker_factory: Callable[[], EntidadWorkerPort],
        concurrencia_maxima: int = 4,
    ) -> None:
        if concurrencia_maxima < 1:
            raise ValueError("concurrencia_maxima debe ser >= 1")
        self._worker_factory = worker_factory
        self._concurrencia_maxima = concurrencia_maxima

    def ejecutar(self, entidades: list[Entidad]) -> ResumenEjecucionPipelineDTO:
        iniciado_en = datetime.now(UTC)
        logger.info(
            "pipeline_descubrimiento_iniciado",
            total_entidades=len(entidades),
            concurrencia_maxima=self._concurrencia_maxima,
        )

        resultados = self._procesar_en_paralelo(entidades)

        finalizado_en = datetime.now(UTC)
        resumen = self._construir_resumen(entidades, resultados, iniciado_en, finalizado_en)

        logger.info(
            "pipeline_descubrimiento_finalizado",
            total_entidades=resumen.total_entidades,
            publicaciones_encontradas=resumen.publicaciones_encontradas,
            documentos_encontrados=resumen.documentos_encontrados,
            errores=resumen.errores,
            duracion_segundos=round(resumen.duracion_segundos, 3),
        )
        return resumen

    def _procesar_en_paralelo(
        self, entidades: list[Entidad]
    ) -> list[ResultadoDescubrimientoEntidadDTO]:
        if not entidades:
            return []

        cola_trabajo: queue.Queue[Entidad | None] = queue.Queue()
        for entidad in entidades:
            cola_trabajo.put(entidad)

        cantidad_hilos = min(self._concurrencia_maxima, len(entidades))
        for _ in range(cantidad_hilos):
            cola_trabajo.put(_SENTINEL_FIN_DE_COLA)

        resultados: list[ResultadoDescubrimientoEntidadDTO] = []
        lock_resultados = threading.Lock()

        def _ejecutar_hilo_worker() -> None:
            # Worker creado de forma perezosa (solo si a este hilo le toca
            # al menos una entidad) y reutilizado para todas las entidades
            # que ese MISMO hilo procese -- ahi vive la reutilizacion del
            # navegador. Se cierra al final, en este mismo hilo.
            worker: EntidadWorkerPort | None = None
            try:
                while True:
                    entidad = cola_trabajo.get()
                    if entidad is _SENTINEL_FIN_DE_COLA:
                        return
                    if worker is None:
                        worker = self._worker_factory()
                    resultado = self._procesar_con_defensa(worker, entidad)
                    with lock_resultados:
                        resultados.append(resultado)
            finally:
                if worker is not None:
                    worker.cerrar()

        hilos = [
            threading.Thread(target=_ejecutar_hilo_worker, name=f"descubrimiento-worker-{i}", daemon=True)
            for i in range(cantidad_hilos)
        ]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()

        return resultados

    @staticmethod
    def _procesar_con_defensa(
        worker: EntidadWorkerPort, entidad: Entidad
    ) -> ResultadoDescubrimientoEntidadDTO:
        """Ultima linea de defensa: ni siquiera un bug inesperado del
        worker debe tumbar el hilo (y con el, el resto de su cola)."""
        try:
            return worker.procesar(entidad)
        except Exception as exc:  # noqa: BLE001
            logger.error("error_inesperado_procesando_entidad", entidad=entidad.nombre, error=str(exc))
            return ResultadoDescubrimientoEntidadDTO(
                entidad=entidad,
                publicacion=None,
                documento=None,
                exito=False,
                error=f"error inesperado: {exc}",
            )

    @staticmethod
    def _construir_resumen(
        entidades: list[Entidad],
        resultados: list[ResultadoDescubrimientoEntidadDTO],
        iniciado_en: datetime,
        finalizado_en: datetime,
    ) -> ResumenEjecucionPipelineDTO:
        publicaciones = sum(1 for r in resultados if r.publicacion is not None)
        documentos = sum(1 for r in resultados if r.documento is not None)
        errores = sum(1 for r in resultados if not r.exito)
        return ResumenEjecucionPipelineDTO(
            total_entidades=len(entidades),
            publicaciones_encontradas=publicaciones,
            documentos_encontrados=documentos,
            errores=errores,
            iniciado_en=iniciado_en,
            finalizado_en=finalizado_en,
        )
