"""Punto de entrada FastAPI -- Modulo 10 (API REST).

    uvicorn govdata.infrastructure.api.app:app --host 0.0.0.0 --port 8000

Arma la app: routers (`/api/v1/...`), middleware (request-id, rate limit,
CORS), manejo global de errores y metadata de OpenAPI. NO instancia
`Container` directamente en este modulo salvo para leer `ApiSettings` --
cada request abre su propia `Session` via `dependencies.get_sesion`."""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from govdata.config.settings import ApiSettings, get_settings
from govdata.infrastructure.api.dependencies import requerir_sesion
from govdata.domain.exceptions.domain_exceptions import GovDataError
from govdata.infrastructure.api.exception_handlers import (
    manejar_error_inesperado,
    manejar_error_validacion,
    manejar_govdata_error,
    manejar_http_exception,
)
from govdata.infrastructure.api.middleware.rate_limit import RateLimitMiddleware
from govdata.infrastructure.api.middleware.request_id import RequestIdMiddleware
from govdata.infrastructure.api.routes import abogados, auditores, auth, companias, entidades, funcionarios, jobs, sistema

_DESCRIPCION = """
Capa de acceso y entrega de GovData Intelligence Platform (Modulo 10).

Compone lo que los Modulos 1-9 (congelados) ya calculan -- descubrimiento
y monitoreo de Transparencia, identidad maestra, SENESCYT, Foro de
Abogados y el Orquestador Maestro -- para que un cliente HTTP obtenga,
con una unica llamada, el perfil consolidado de los funcionarios
juridicos de una entidad publica. Esta API NUNCA reimplementa scraping,
extraccion, resolucion de identidad ni el pipeline de orquestacion.
"""

_TAGS_METADATA = [
    {"name": "Sistema", "description": "Salud del proceso, disponibilidad y bienvenida."},
    {"name": "Entidades", "description": "Instituciones publicas, consulta consolidada y su historial."},
    {"name": "Funcionarios", "description": "Perfil consolidado por funcionario (persona_master_id)."},
    {"name": "Jobs", "description": "Estado de trabajos del Orquestador Maestro (Modulo 9)."},
]


def crear_app(api_settings: ApiSettings | None = None) -> FastAPI:
    """`api_settings` es inyectable (por defecto `None` -- usa la
    configuracion real, `get_settings().api`) unicamente para que los
    tests puedan construir una app con, por ejemplo, un rate limit bajo
    controlado, sin mutar variables de entorno globales."""
    api_settings = api_settings or get_settings().api

    app = FastAPI(
        title="GovData Intelligence Platform API",
        description=_DESCRIPCION,
        version=api_settings.version,
        openapi_tags=_TAGS_METADATA,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Orden de middleware: se ejecutan de AFUERA hacia ADENTRO en el orden
    # en que se agregan -- RequestId primero (para que rate-limit/errores
    # ya tengan `request.state.request_id` disponible).
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RateLimitMiddleware, limite_por_minuto=api_settings.rate_limit_por_minuto)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.origenes_cors,
        allow_credentials=api_settings.origenes_cors != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(GovDataError, manejar_govdata_error)
    app.add_exception_handler(RequestValidationError, manejar_error_validacion)
    app.add_exception_handler(StarletteHTTPException, manejar_http_exception)
    app.add_exception_handler(Exception, manejar_error_inesperado)

    app.include_router(sistema.router)
    app.include_router(auth.router, prefix="/api/v1")
    protegido = [Depends(requerir_sesion)]
    app.include_router(abogados.router, prefix="/api/v1", dependencies=protegido)
    app.include_router(auditores.router, prefix="/api/v1", dependencies=protegido)
    app.include_router(companias.router, prefix="/api/v1", dependencies=protegido)
    app.include_router(entidades.router, prefix="/api/v1", dependencies=protegido)
    app.include_router(funcionarios.router, prefix="/api/v1", dependencies=protegido)
    app.include_router(jobs.router, prefix="/api/v1", dependencies=protegido)

    return app


app = crear_app()
