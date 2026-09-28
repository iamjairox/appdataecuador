"""Rate limiter thread-safe compartido entre workers concurrentes.

Simple limitador de "intervalo minimo entre llamadas", no un token-bucket
completo -- suficiente para no saturar el portal de origen sin agregar
complejidad innecesaria. Es thread-safe porque `PipelineOrchestratorService`
comparte una unica instancia entre todos los workers del pool de hilos, que
es precisamente el punto: el limite aplica al portal como un todo, no por
hilo.
"""

from __future__ import annotations

import threading
import time


class RateLimiter:
    """Garantiza que las llamadas (de todos los hilos) queden espaciadas
    por al menos `intervalo_minimo_segundos`.
    """

    def __init__(self, intervalo_minimo_segundos: float) -> None:
        if intervalo_minimo_segundos < 0:
            raise ValueError("intervalo_minimo_segundos no puede ser negativo")
        self._intervalo = intervalo_minimo_segundos
        self._lock = threading.Lock()
        self._ultima_llamada: float | None = None

    def esperar_turno(self) -> None:
        """Bloquea el hilo llamante lo necesario para respetar el intervalo."""
        with self._lock:
            ahora = time.monotonic()
            if self._ultima_llamada is not None:
                transcurrido = ahora - self._ultima_llamada
                faltante = self._intervalo - transcurrido
                if faltante > 0:
                    time.sleep(faltante)
            self._ultima_llamada = time.monotonic()
