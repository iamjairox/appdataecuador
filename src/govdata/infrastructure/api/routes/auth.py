"""Inicio y cierre de sesión para la única cuenta compartida de DataOK."""
from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from govdata.config.settings import Settings
from govdata.infrastructure.api.auth import crear_token, leer_token, verificar_clave
from govdata.infrastructure.api.dependencies import get_settings_dep

router = APIRouter(prefix="/auth", tags=["Acceso"])
_COOKIE = "dataok_session"


class Credenciales(BaseModel):
    usuario: str = Field(min_length=1, max_length=100)
    clave: str = Field(min_length=1, max_length=300)


def _configurado(settings: Settings) -> bool:
    acceso = settings.acceso
    return settings.acceso_requerido and bool(acceso.usuario and acceso.clave_hash.get_secret_value() and acceso.secreto.get_secret_value())


@router.get("/estado")
def estado_acceso(request: Request, settings: Annotated[Settings, Depends(get_settings_dep)]) -> dict:
    if not settings.acceso_requerido:
        return {"requerido": False, "autenticado": True}
    if not _configurado(settings):
        return {"requerido": True, "autenticado": False, "configurado": False}
    usuario = leer_token(request.cookies.get(_COOKIE), settings.acceso.secreto.get_secret_value())
    return {"requerido": True, "autenticado": usuario == settings.acceso.usuario, "configurado": True}


@router.post("/ingresar")
def ingresar(credenciales: Credenciales, response: Response, settings: Annotated[Settings, Depends(get_settings_dep)]) -> dict:
    if not _configurado(settings):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="El acceso aún no está configurado en el servidor.")
    acceso = settings.acceso
    valido = hmac.compare_digest(credenciales.usuario, acceso.usuario) and verificar_clave(credenciales.clave, acceso.clave_hash.get_secret_value())
    if not valido:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o clave incorrectos.")
    response.set_cookie(
        key=_COOKIE,
        value=crear_token(acceso.usuario, acceso.secreto.get_secret_value(), acceso.duracion_horas * 3600),
        max_age=acceso.duracion_horas * 3600,
        httponly=True,
        secure=settings.es_produccion(),
        samesite="lax",
        path="/",
    )
    return {"autenticado": True}


@router.post("/salir")
def salir(response: Response) -> dict:
    response.delete_cookie(_COOKIE, path="/")
    return {"autenticado": False}
