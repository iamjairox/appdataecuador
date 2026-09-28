"""Fixtures compartidas para tests de integracion (persistencia).

Usa SQLite en memoria en lugar de PostgreSQL real: para el Modulo 1 lo
que se prueba es que el mapeo ORM <-> dominio y los repositorios
funcionan correctamente, no las particularidades de un motor especifico.
Los tests contra PostgreSQL real (con Testcontainers o una instancia de
CI) se agregan en modulos posteriores cuando haya logica especifica del
dialecto (ej. JSONB, indices GIN para busqueda de texto).
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, BrowserContext, sync_playwright
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from govdata.infrastructure.persistence.postgresql.models import Base
from tests.integration.descarga_fixture_server import DescargaFixtureServer
from tests.integration.dpe_fixture_server import DpeFixtureServer


@pytest.fixture()
def sqlite_engine():
    """SQLite en memoria de UN SOLO HILO (StaticPool). Para tests que NO
    ejercitan concurrencia real -- ver `sqlite_engine_multihilo` para eso.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def sqlite_engine_multihilo() -> Iterator:
    """SQLite respaldado por ARCHIVO temporal (no ":memory:"), para tests
    que si ejercitan hilos concurrentes reales (ej. `PipelineOrchestratorService`
    con `concurrencia_maxima > 1`).

    Se detecto empiricamente (corrida manual, no en la suite de pytest) que
    ":memory:" + `StaticPool` fuerza a TODOS los hilos a compartir la MISMA
    conexion DBAPI fisica -- el modulo `sqlite3` no es seguro para uso
    verdaderamente concurrente sobre una unica conexion (aunque
    `check_same_thread=False` lo permita), y produjo intermitentemente
    `This result object does not return rows` bajo carrera. Un archivo
    SQLite real permite que cada hilo abra su PROPIA conexion (pool normal)
    contra el mismo archivo, que es como se comporta PostgreSQL en
    produccion (cada sesion = conexion real independiente).
    """
    descriptor, ruta = tempfile.mkstemp(suffix=".sqlite3")
    os.close(descriptor)
    try:
        engine = create_engine(f"sqlite:///{ruta}", future=True)
        Base.metadata.create_all(engine)
        yield engine
        engine.dispose()
    finally:
        os.remove(ruta)


@pytest.fixture()
def sesion(sqlite_engine) -> Iterator[Session]:
    Factory = sessionmaker(bind=sqlite_engine, future=True)
    sesion = Factory()
    try:
        yield sesion
    finally:
        sesion.close()


@pytest.fixture(scope="session")
def navegador() -> Iterator[Browser]:
    """Un unico Chromium headless para toda la sesion de tests (caro de
    lanzar; se reutiliza igual que en produccion -- ver BrowserManager)."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture()
def contexto_navegador(navegador: Browser) -> Iterator[BrowserContext]:
    contexto = navegador.new_context()
    yield contexto
    contexto.close()


@pytest.fixture()
def servidor_fixtures_dpe() -> Iterator[DpeFixtureServer]:
    """Servidor HTTP local (modo simulacion) con las fixtures del portal DPE."""
    servidor = DpeFixtureServer()
    servidor.iniciar()
    yield servidor
    servidor.detener()


@pytest.fixture()
def servidor_fixtures_descarga() -> Iterator[DescargaFixtureServer]:
    """Servidor HTTP local (modo simulacion) con las fixtures de descarga
    (Modulo 3): 200/404/500/timeout/pagina-de-error/corrupto."""
    servidor = DescargaFixtureServer()
    servidor.iniciar()
    yield servidor
    servidor.detener()


@pytest.fixture()
def directorio_storage_temporal() -> Iterator[str]:
    """Directorio temporal para `LocalFileStorageAdapter` en tests."""
    with tempfile.TemporaryDirectory(prefix="govdata-storage-") as ruta:
        yield ruta
