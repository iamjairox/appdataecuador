"""Rutas: Sistema -- Submodulos 10.16/10.19 (health/ready/bienvenida)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from govdata.config.settings import ApiSettings, Settings
from govdata.infrastructure.api.dependencies import get_api_settings, get_sesion, get_settings_dep

router = APIRouter(tags=["Sistema"])


@router.get(
    "/health",
    summary="Estado de vida del proceso",
    description="Verificacion minima: el proceso esta vivo y respondiendo. No consulta la base de "
    "datos ni dependencias externas (SENESCYT/Foro) -- para eso ver `/ready`.",
)
def health(settings: Annotated[Settings, Depends(get_settings_dep)]) -> dict:
    return {
        "status": "ok",
        "service": "govdata-api",
        "version": settings.api.version,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get(
    "/ready",
    summary="Disponibilidad para recibir trafico",
    description="Comprueba configuracion valida y conexion real a PostgreSQL. NUNCA llama a "
    "SENESCYT/Foro de Abogados (Submodulo 10.16: 'no hacer consultas externas en cada health check').",
)
def ready(
    settings: Annotated[Settings, Depends(get_settings_dep)],
    sesion: Annotated[Session, Depends(get_sesion)],
) -> dict:
    sesion.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "service": "govdata-api",
        "version": settings.api.version,
        "checks": {"configuracion": "ok", "base_de_datos": "ok"},
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get(
    "/",
    summary="Bienvenida",
    description="Pagina minima de bienvenida -- el Modulo 10 prioriza la API REST + Swagger, "
    "no un frontend (ver Submodulo 10.19; el frontend completo queda para un modulo futuro).",
)
def bienvenida(api_settings: Annotated[ApiSettings, Depends(get_api_settings)]) -> dict:
    return {
        "nombre": "GovData Intelligence Platform",
        "version": api_settings.version,
        "estado": "operativo",
        "documentacion": {"swagger": "/docs", "redoc": "/redoc", "openapi": "/openapi.json"},
    }
