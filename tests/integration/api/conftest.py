"""Fixtures compartidas para los tests de integracion del Modulo 10 (API REST).

`cliente` reutiliza la fixture `sesion` (SQLite en memoria, `StaticPool`)
YA DEFINIDA en `tests/integration/conftest.py` -- la unica dependencia que
se sobreescribe es `get_sesion` (FastAPI `dependency_overrides`, la forma
IDIOMATICA de inyectar test doubles sin monkeypatchear modulos). El resto
de las rutas siguen llamando `Container` de verdad, pero como SIEMPRE
reciben la `sesion` de test por parametro (nunca abren la suya propia),
terminan operando sobre la misma base SQLite -- ver `dependencies.py`."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from govdata.infrastructure.api import dependencies as deps
from govdata.infrastructure.api.app import crear_app


@pytest.fixture()
def cliente(sesion: Session) -> Iterator[TestClient]:
    app = crear_app()

    def _get_sesion_override() -> Iterator[Session]:
        yield sesion

    app.dependency_overrides[deps.get_sesion] = _get_sesion_override
    # `raise_server_exceptions=False`: sin esto, un 500 real (excepcion no
    # prevista) se re-lanza hacia el propio test en vez de llegar como
    # respuesta HTTP -- necesario para poder probar el manejador generico
    # (`manejar_error_inesperado`) igual que lo veria un cliente real.
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()
