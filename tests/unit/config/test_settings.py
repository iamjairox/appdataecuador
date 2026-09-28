"""Tests: Config Manager multi-entorno."""

from __future__ import annotations

import pytest

from govdata.config.settings import get_settings, reset_settings_cache
from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError

_CLAVES_A_LIMPIAR = [
    "APP_ENV",
    "DB_HOST",
    "DB_NOMBRE",
    "DB_ECHO_SQL",
    "LOG_NIVEL",
    "PLAYWRIGHT_HEADLESS",
]


@pytest.fixture(autouse=True)
def _entorno_limpio(monkeypatch: pytest.MonkeyPatch):
    for clave in _CLAVES_A_LIMPIAR:
        monkeypatch.delenv(clave, raising=False)
    reset_settings_cache()
    yield
    reset_settings_cache()


def test_carga_env_test_segun_app_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    settings = get_settings()

    assert settings.app_env == "test"
    assert settings.database.nombre == "govdata_test"
    assert settings.scraping.max_reintentos == 1


def test_carga_env_development_por_defecto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    settings = get_settings()

    assert settings.database.nombre == "govdata_dev"
    assert settings.playwright.headless is False


def test_variable_de_entorno_real_tiene_prioridad_sobre_archivo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DB_HOST", "host-forzado-por-ci")
    settings = get_settings()

    assert settings.database.host == "host-forzado-por-ci"


def test_app_env_invalido_lanza_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "produccion-mal-escrito")
    with pytest.raises(ConfiguracionInvalidaError):
        get_settings()


def test_dsn_se_construye_correctamente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    settings = get_settings()

    assert settings.database.dsn.startswith("postgresql+psycopg2://")
    assert "govdata_test" in settings.database.dsn
