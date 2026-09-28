"""Middleware: RequestIdMiddleware -- Submodulo 10.12 (Observabilidad).

Cada peticion tiene un `request_id`: si el cliente envia `X-Request-ID`
(y es un valor "seguro" -- alfanumerico/guiones, largo acotado, para
evitar inyectar texto arbitrario en logs), se reutiliza; si no, se genera
un UUID4 nuevo. Se expone en `request.state.request_id` (lo leen
`exception_handlers.py` y las rutas para incluirlo en las respuestas de
error) y siempre se devuelve en el header `X-Request-ID` de la
respuesta."""

from __future__ import annotations

import re
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from govdata.config.logging_config import get_logger

logger = get_logger(__name__)

_REQUEST_ID_VALIDO = re.compile(r"^[a-zA-Z0-9._-]{1,128}$")


def _request_id_entrante_o_nuevo(valor: str | None) -> str:
    if valor and _REQUEST_ID_VALIDO.match(valor):
        return valor
    return str(uuid.uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = _request_id_entrante_o_nuevo(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id

        logger.info(
            "api_request_iniciada", request_id=request_id, metodo=request.method, path=str(request.url.path),
        )
        respuesta = await call_next(request)
        respuesta.headers["X-Request-ID"] = request_id
        logger.info(
            "api_request_finalizada", request_id=request_id, metodo=request.method,
            path=str(request.url.path), status_code=respuesta.status_code,
        )
        return respuesta
