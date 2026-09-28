"""Middleware: RateLimitMiddleware -- Submodulo 10.22.

Proteccion BASICA contra abuso, sin Redis: ventana deslizante en memoria,
protegida por un `threading.Lock` (mismo criterio que `RateLimiter`,
Modulo 2, para el scraping del portal DPE -- un unico contador
compartido, seguro entre hilos). Limite configurable
(`RATE_LIMIT_POR_MINUTO`).

LIMITACION DOCUMENTADA (Submodulo 10.22, explicita en la especificacion):
este contador es POR PROCESO. Un despliegue multi-instancia (varios
workers Uvicorn/Gunicorn, o varios contenedores detras de un balanceador)
necesitara un backend distribuido (Redis) para que el limite sea
GLOBAL -- fuera de alcance del Modulo 10, no se introduce Redis "por
costumbre" para una unica instancia."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

_VENTANA_SEGUNDOS = 60.0


class ContadorVentanaDeslizante:
    """Cuenta peticiones por clave (API key o IP) en los ultimos 60s."""

    def __init__(self, limite_por_minuto: int) -> None:
        self._limite = limite_por_minuto
        self._lock = threading.Lock()
        self._peticiones: dict[str, deque[float]] = defaultdict(deque)

    def permitir(self, clave: str) -> bool:
        ahora = time.monotonic()
        with self._lock:
            marcas = self._peticiones[clave]
            while marcas and ahora - marcas[0] > _VENTANA_SEGUNDOS:
                marcas.popleft()
            if len(marcas) >= self._limite:
                return False
            marcas.append(ahora)
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, limite_por_minuto: int) -> None:
        super().__init__(app)
        self._contador = ContadorVentanaDeslizante(limite_por_minuto)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        clave = request.headers.get("X-API-Key") or (request.client.host if request.client else "anonimo")
        if not self._contador.permitir(clave):
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "codigo": "RATE_LIMIT_EXCEDIDO",
                        "mensaje": "Demasiadas peticiones. Intenta de nuevo en un momento.",
                        "detalle": None,
                        "request_id": request_id,
                    }
                },
            )
        return await call_next(request)
