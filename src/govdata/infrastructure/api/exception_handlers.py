"""Manejo global de errores -- Submodulo 10.11.

Traduce la jerarquia de excepciones de dominio (Modulos 1-9, congelada,
`domain.exceptions.domain_exceptions`) a respuestas HTTP estandar. NINGUNA
excepcion interna se devuelve directamente al cliente (nunca stack traces,
nunca mensajes de SQLAlchemy/Playwright/requests crudos).

Forma EXACTA de error pedida por la especificacion:

    {"error": {"codigo": "ENTIDAD_NO_ENCONTRADA", "mensaje": "...",
                "detalle": null, "request_id": "..."}}

`CODIGO_HTTP_POR_EXCEPCION` se recorre en orden -- las excepciones mas
ESPECIFICAS van primero; `GovDataError` (base) es el fallback universal a
500. No es necesario listar aqui las ~50 subclases de excepcion del
sistema una por una: solo las que la API puede genuinamente encontrar en
sus flujos (buscar entidad/funcionario/job, orquestar, exportar); el resto
cae correctamente en el fallback 500 sin perder informacion (el
`codigo` sigue siendo el nombre exacto de la excepcion)."""

from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from govdata.config.logging_config import get_logger
from govdata.domain.exceptions.domain_exceptions import (
    BloqueoOptimistaFallidoError,
    ConfiguracionInvalidaError,
    ConsultaForoFallidaError,
    ConsultaForoPermanenteError,
    ConsultaSenescytFallidaError,
    DescargaFallidaError,
    DocumentoNoSoportadoError,
    DocumentoYaEnProcesoError,
    EnriquecimientoAcademicoFallidoError,
    EnriquecimientoForoFallidoError,
    EntidadInvalidaError,
    EntidadNoEncontradaError,
    ForoCircuitoAbiertoError,
    FuncionarioInvalidoError,
    GovDataError,
    OrquestacionFallidaError,
    PersistenciaError,
    PersonaInvalidaError,
    PersonaMasterInvalidaError,
    PlanEjecucionInvalidoError,
    PoliticaEjecucionInvalidaError,
    PresupuestoReintentosAgotadoError,
    PublicacionNoDisponibleError,
    RecursoNoDisponibleError,
    TrabajoOrquestadorInvalidoError,
    ValorInvalidoError,
)

logger = get_logger(__name__)

# Orden: mas ESPECIFICO primero. `GovDataError` (base) SIEMPRE al final.
CODIGO_HTTP_POR_EXCEPCION: tuple[tuple[type[GovDataError], int], ...] = (
    # -- 404: recurso inexistente --------------------------------------
    (EntidadNoEncontradaError, status.HTTP_404_NOT_FOUND),
    (PersonaMasterInvalidaError, status.HTTP_404_NOT_FOUND),
    (PublicacionNoDisponibleError, status.HTTP_404_NOT_FOUND),
    (RecursoNoDisponibleError, status.HTTP_404_NOT_FOUND),
    # -- 409: conflicto / operacion incompatible con el estado actual --
    (BloqueoOptimistaFallidoError, status.HTTP_409_CONFLICT),
    (TrabajoOrquestadorInvalidoError, status.HTTP_409_CONFLICT),
    (PlanEjecucionInvalidoError, status.HTTP_409_CONFLICT),
    (DocumentoYaEnProcesoError, status.HTTP_409_CONFLICT),
    (PresupuestoReintentosAgotadoError, status.HTTP_409_CONFLICT),
    # -- 400: entrada invalida (datos de negocio, no de forma/schema) --
    (ValorInvalidoError, status.HTTP_400_BAD_REQUEST),
    (EntidadInvalidaError, status.HTTP_400_BAD_REQUEST),
    (PersonaInvalidaError, status.HTTP_400_BAD_REQUEST),
    (FuncionarioInvalidoError, status.HTTP_400_BAD_REQUEST),
    (DocumentoNoSoportadoError, status.HTTP_400_BAD_REQUEST),
    (PoliticaEjecucionInvalidaError, status.HTTP_400_BAD_REQUEST),
    # -- 502: dependencia externa fallo de forma no reintentable --------
    (ConsultaForoPermanenteError, status.HTTP_502_BAD_GATEWAY),
    (EnriquecimientoAcademicoFallidoError, status.HTTP_502_BAD_GATEWAY),
    (EnriquecimientoForoFallidoError, status.HTTP_502_BAD_GATEWAY),
    # -- 503: dependencia externa temporalmente no disponible -----------
    (ForoCircuitoAbiertoError, status.HTTP_503_SERVICE_UNAVAILABLE),
    (ConsultaForoFallidaError, status.HTTP_503_SERVICE_UNAVAILABLE),
    (ConsultaSenescytFallidaError, status.HTTP_503_SERVICE_UNAVAILABLE),
    (DescargaFallidaError, status.HTTP_503_SERVICE_UNAVAILABLE),
    # -- 500: error interno (persistencia, configuracion, orquestacion --
    # -- generica sin clasificar arriba) ---------------------------------
    (PersistenciaError, status.HTTP_500_INTERNAL_SERVER_ERROR),
    (ConfiguracionInvalidaError, status.HTTP_500_INTERNAL_SERVER_ERROR),
    (OrquestacionFallidaError, status.HTTP_500_INTERNAL_SERVER_ERROR),
    # -- Fallback universal: cualquier otra subclase de GovDataError ----
    (GovDataError, status.HTTP_500_INTERNAL_SERVER_ERROR),
)


def _codigo_http(error: GovDataError) -> int:
    for tipo_excepcion, codigo in CODIGO_HTTP_POR_EXCEPCION:
        if isinstance(error, tipo_excepcion):
            return codigo
    return status.HTTP_500_INTERNAL_SERVER_ERROR  # pragma: no cover -- GovDataError ya cubre todo


def _cuerpo_error(codigo: str, mensaje: str, request: Request, detalle: str | None = None) -> dict:
    request_id = getattr(request.state, "request_id", None)
    return {"error": {"codigo": codigo, "mensaje": mensaje, "detalle": detalle, "request_id": request_id}}


async def manejar_govdata_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, GovDataError)
    codigo_http = _codigo_http(exc)
    logger.warning(
        "api_error_dominio", tipo=type(exc).__name__, codigo_http=codigo_http, mensaje=str(exc),
        request_id=getattr(request.state, "request_id", None), path=str(request.url.path),
    )
    return JSONResponse(
        status_code=codigo_http,
        content=_cuerpo_error(type(exc).__name__, str(exc), request),
    )


async def manejar_error_validacion(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_cuerpo_error(
            "VALIDACION_INVALIDA", "Los parametros de la peticion no son validos.", request,
            detalle=str(exc.errors()),
        ),
    )


async def manejar_http_exception(request: Request, exc: Exception) -> JSONResponse:
    """Normaliza las `HTTPException` lanzadas explicitamente por las
    rutas/dependencias (401 API key, 404 job/recurso puntual, 422
    paginacion) a la MISMA forma de error que el resto de la API."""
    assert isinstance(exc, StarletteHTTPException)
    return JSONResponse(
        status_code=exc.status_code,
        content=_cuerpo_error(f"HTTP_{exc.status_code}", str(exc.detail), request),
        headers=exc.headers,
    )


async def manejar_error_inesperado(request: Request, exc: Exception) -> JSONResponse:
    """Ultimo recurso: cualquier excepcion NO prevista (nunca deberia
    llegar aqui en producto, pero nunca se expone el stack trace real al
    cliente si sucede)."""
    logger.error(
        "api_error_inesperado", tipo=type(exc).__name__, mensaje=str(exc),
        request_id=getattr(request.state, "request_id", None), path=str(request.url.path),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_cuerpo_error("ERROR_INTERNO", "Ocurrio un error interno inesperado.", request),
    )
