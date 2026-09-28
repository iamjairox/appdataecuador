"""Politica de reintentos compartida (basada en tenacity).

Los errores TRANSITORIOS (red, timeouts, descargas) se reintentan con
backoff exponencial + jitter. Los errores PERMANENTES (dato invalido,
formato no soportado) NUNCA se reintentan -- ver la convencion documentada
en `domain.exceptions.domain_exceptions`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from govdata.config.logging_config import get_logger
from govdata.domain.exceptions.domain_exceptions import (
    DescargaFallidaError,
    EntidadNoEncontradaError,
    GovDataError,
)

logger = get_logger(__name__)

T = TypeVar("T")

# Excepciones consideradas transitorias por defecto (reintentables).
ERRORES_TRANSITORIOS: tuple[type[Exception], ...] = (
    DescargaFallidaError,
    EntidadNoEncontradaError,
    ConnectionError,
    TimeoutError,
)


def con_reintentos(
    max_intentos: int = 3,
    espera_inicial_segundos: float = 2.0,
    espera_maxima_segundos: float = 30.0,
    errores_reintentables: tuple[type[Exception], ...] = ERRORES_TRANSITORIOS,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorador de reintento con backoff exponencial + jitter.

    Uso:
        @con_reintentos(max_intentos=3)
        def descargar(url: str) -> bytes: ...
    """

    def _antes_de_reintentar(estado: RetryCallState) -> None:  # pragma: no cover - logging puro
        excepcion = estado.outcome.exception() if estado.outcome else None
        logger.warning(
            "reintentando_operacion",
            funcion=estado.fn.__name__ if estado.fn else "desconocida",
            intento=estado.attempt_number,
            error=str(excepcion) if excepcion else None,
        )

    return retry(
        stop=stop_after_attempt(max_intentos),
        wait=wait_exponential_jitter(
            initial=espera_inicial_segundos, max=espera_maxima_segundos
        ),
        retry=retry_if_exception_type(errores_reintentables),
        before_sleep=_antes_de_reintentar,
        reraise=True,
    )


def es_error_permanente(error: Exception) -> bool:
    """True si el error NO debe reintentarse (dato/formato invalido)."""
    return isinstance(error, GovDataError) and not isinstance(error, ERRORES_TRANSITORIOS)
