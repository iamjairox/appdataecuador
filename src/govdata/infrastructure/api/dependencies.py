"""Dependencias de FastAPI -- el UNICO lugar del Modulo 10 que conoce
`Container` (Modulo 1, congelado). Las rutas nunca instancian `Session`,
repositorios ni servicios directamente: siempre reciben lo que necesitan
via `Depends(...)` sobre las funciones de este archivo.

Una `Session` por PETICION HTTP (Unit of Work): se abre al entrar al
endpoint y se hace commit/rollback/close automaticamente al salir --
mismo patron `sesion_scope` que ya usan los scripts CLI (`Container.nueva_sesion`),
solo que aqui el "with" lo maneja FastAPI a traves de un dependency
generador."""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from govdata.application.services.govdata_pipeline_orchestrator import GovDataPipelineOrchestrator
from govdata.config.container import Container
from govdata.config.settings import ApiSettings, Settings, get_settings


@lru_cache(maxsize=1)
def get_container() -> Container:
    """Un unico `Container` por proceso (mismo criterio que `get_settings`,
    Modulo 1) -- cachea `engine`/`session_factory`, nunca reabre conexiones
    de mas."""
    return Container()


def get_settings_dep() -> Settings:
    return get_settings()


def get_api_settings() -> ApiSettings:
    return get_settings().api


def get_sesion() -> Iterator[Session]:
    """Una `Session` (Unit of Work) por peticion HTTP. Commit automatico
    si el endpoint termina sin excepcion, rollback si lanza -- ver
    `sesion_scope` (Modulo 1, congelado, `infrastructure/persistence/postgresql/database.py`)."""
    container = get_container()
    with container.nueva_sesion() as sesion:
        yield sesion


def verificar_api_key(
    api_settings: Annotated[ApiSettings, Depends(get_api_settings)],
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Submodulo 10.10 (Seguridad): API Key configurable por entorno.

    Si `API_KEY` no esta configurada (cadena vacia -- valor por defecto en
    `development`), la verificacion queda deshabilitada. En `production`
    la variable de entorno DEBE configurarse (ver `.env.production`,
    plantilla con `CAMBIAR_ME`). `api_settings` se recibe via `Depends`
    (en vez de llamar `get_api_settings()` directo) para que sea
    sobreescribible con `app.dependency_overrides` en tests."""
    if not api_settings.api_key_requerida:
        return
    if x_api_key is None or x_api_key != api_settings.api_key.get_secret_value():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key invalida o ausente")


class ParametrosPaginacion:
    """Submodulo 10.8: `page >= 1`, `1 <= page_size <= page_size_maximo`
    (configurable, `RATE_LIMIT_PAGINA_MAXIMA`) -- FastAPI valida los
    limites INFERIORES via `Query(ge=...)`; el limite SUPERIOR depende de
    configuracion, por eso se aplica aqui, no en la firma del `Query`."""

    def __init__(
        self,
        api_settings: Annotated[ApiSettings, Depends(get_api_settings)],
        page: int = Query(default=1, ge=1, description="Numero de pagina (1-indexado)"),
        page_size: int = Query(default=50, ge=1, description="Cantidad de items por pagina"),
    ) -> None:
        maximo = api_settings.rate_limit_pagina_maxima
        if page_size > maximo:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"page_size no puede superar {maximo}",
            )
        self.page = page
        self.page_size = page_size


def get_orquestador(
    sesion: Annotated[Session, Depends(get_sesion)],
) -> GovDataPipelineOrchestrator:
    """Submodulo 10.28 (regla del pipeline): el UNICO punto de entrada al
    motor -- las rutas de `entidades.py` nunca llaman descubrimiento/
    descarga/extraccion/SENESCYT/Foro por separado, solo este orquestador
    (Modulo 9, congelado)."""
    return get_container().crear_govdata_pipeline_orchestrator(sesion)
