"""Config Manager centralizado.

Carga configuracion desde variables de entorno / archivos `.env.<entorno>`
segun la variable `APP_ENV` (development | test | production). Nada en el
resto del sistema debe leer `os.environ` directamente: todo pasa por
`get_settings()`, que ademas cachea la instancia (proceso completo usa la
misma configuracion, evitando relecturas inconsistentes a mitad de una
corrida larga).

Uso:
    from govdata.config.settings import get_settings
    settings = get_settings()
    settings.database.dsn
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError

_ENTORNOS_VALIDOS = {"development", "test", "production"}
_RAIZ_PROYECTO = Path(__file__).resolve().parents[3]


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore")

    host: str = "localhost"
    port: int = 5432
    nombre: str = "govdata"
    usuario: str = "govdata"
    password: SecretStr = SecretStr("govdata")
    pool_size: int = 10
    max_overflow: int = 5
    echo_sql: bool = False

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+psycopg2://{self.usuario}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.nombre}"
        )


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")

    host: str = "localhost"
    port: int = 6379
    db: int = 0

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


class MinioSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MINIO_", extra="ignore")

    endpoint: str = "localhost:9000"
    access_key: str = "govdata"
    secret_key: SecretStr = SecretStr("govdata123")
    bucket: str = "documentos-transparencia"
    usar_ssl: bool = False


class PlaywrightSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PLAYWRIGHT_", extra="ignore")

    headless: bool = True
    timeout_ms: int = 30_000
    navegador: str = "chromium"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GovDataIntelligencePlatform/1.0"
    )


class ScrapingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SCRAPING_", extra="ignore")

    url_base_dpe: str = "https://transparencia.dpe.gob.ec/entidades"
    url_origen_dpe: str = "https://transparencia.dpe.gob.ec"
    concurrencia_maxima: int = 4
    max_reintentos: int = 3
    backoff_base_segundos: float = 2.0
    intervalo_minimo_segundos: float = 1.0
    """Rate limiting: tiempo minimo entre peticiones consecutivas al portal."""
    anios_lookback_maximo: int = 3
    """Cuantos anios hacia atras probar si el anio actual no tiene publicaciones."""
    umbral_confianza_item: float = 70.0
    """Score minimo (0-100) de RapidFuzz para aceptar el numeral 'directorio y distributivo'."""
    umbral_confianza_archivo: float = 80.0
    """Score minimo (0-100) de RapidFuzz para aceptar el archivo 'conjunto de datos'."""


class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOG_", extra="ignore")

    nivel: str = "INFO"
    formato_json: bool = False
    ruta_archivo: str = "logs/govdata.log"


class DownloadSettings(BaseSettings):
    """Modulo 3: descarga de documentos."""

    model_config = SettingsConfigDict(env_prefix="DOWNLOAD_", extra="ignore")

    concurrencia_maxima: int = 4
    timeout_segundos: float = 30.0
    max_reintentos: int = 3
    backoff_base_segundos: float = 2.0
    tamano_maximo_bytes: int = 100 * 1024 * 1024
    """Corta la descarga si el archivo supera este tamano (proteccion ante
    respuestas anomalas/maliciosas). 100 MiB por defecto."""
    minutos_liberar_estancados: int = 30
    """Un documento en DESCARGANDO por mas de esto se considera huerfano
    (worker caido) y vuelve a DESCUBIERTO."""
    limite_lote: int = 100
    """Cuantos documentos pendientes se piden por corrida del orquestador."""


class StorageSettings(BaseSettings):
    """Backend de almacenamiento de documentos: `local` o `minio`."""

    model_config = SettingsConfigDict(env_prefix="STORAGE_", extra="ignore")

    backend: str = "local"
    ruta_local: str = "data/documentos"


class ApiSettings(BaseSettings):
    """Modulo 10: API REST -- capa de acceso, nunca reimplementa el motor.

    Nombres de variable EXACTOS pedidos por la especificacion (`APP_HOST`,
    `APP_PORT`, `API_KEY`, `CORS_ORIGINS`, `RATE_LIMIT_POR_MINUTO`) --
    deliberadamente sin un unico `env_prefix` comun (a diferencia de
    `DatabaseSettings`/`ScrapingSettings`/...) porque la especificacion no
    los agrupa bajo un prefijo compartido.

    `api_key` vacio (valor por defecto en `development`) desactiva la
    verificacion -- pensado para desarrollo local; en `production` DEBE
    configurarse via variable de entorno (nunca hardcodeada aqui).
    `cors_origins` es una lista separada por comas."""

    model_config = SettingsConfigDict(extra="ignore")

    host: str = Field(default="0.0.0.0", alias="APP_HOST")
    port: int = Field(default=8000, alias="APP_PORT")
    api_key: SecretStr = Field(default=SecretStr(""), alias="API_KEY")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    rate_limit_por_minuto: int = Field(default=120, alias="RATE_LIMIT_POR_MINUTO")
    rate_limit_pagina_maxima: int = Field(default=100, alias="RATE_LIMIT_PAGINA_MAXIMA")
    version: str = "1.0.0"

    @property
    def origenes_cors(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def api_key_requerida(self) -> bool:
        return bool(self.api_key.get_secret_value())


class Settings(BaseSettings):
    """Configuracion raiz de la aplicacion."""

    model_config = SettingsConfigDict(extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    nombre_app: str = "GovData Intelligence Platform"

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    minio: MinioSettings = Field(default_factory=MinioSettings)
    playwright: PlaywrightSettings = Field(default_factory=PlaywrightSettings)
    scraping: ScrapingSettings = Field(default_factory=ScrapingSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    download: DownloadSettings = Field(default_factory=DownloadSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)

    def es_produccion(self) -> bool:
        return self.app_env == "production"


def _resolver_archivo_env(app_env: str) -> Path | None:
    """Resuelve `.env.<app_env>`; si no existe, cae a `.env`; si tampoco, None."""
    if app_env not in _ENTORNOS_VALIDOS:
        raise ConfiguracionInvalidaError(
            f"APP_ENV invalido: '{app_env}'. Valores permitidos: {sorted(_ENTORNOS_VALIDOS)}"
        )

    candidato_especifico = _RAIZ_PROYECTO / f".env.{app_env}"
    if candidato_especifico.exists():
        return candidato_especifico

    candidato_generico = _RAIZ_PROYECTO / ".env"
    if candidato_generico.exists():
        return candidato_generico

    return None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Construye (una sola vez por proceso) la configuracion de la aplicacion.

    IMPORTANTE: el archivo `.env.<entorno>` resuelto se pasa como
    `_env_file` directamente a cada sub-settings (via pydantic-settings),
    en vez de volcarlo a `os.environ`. Mutar `os.environ` globalmente
    contaminaria el proceso completo de forma permanente (por ejemplo,
    cualquier modulo que dispare `get_settings()` a nivel de import -como
    un logger de modulo- dejaria variables de un entorno pegadas para el
    resto de la ejecucion, incluyendo otros tests). pydantic-settings ya
    resuelve correctamente la prioridad "variable de entorno real >
    archivo .env" sin necesidad de este truco.
    """
    app_env = os.environ.get("APP_ENV", "development")
    archivo_env = _resolver_archivo_env(app_env)
    kwargs_env_file: dict = {"_env_file": archivo_env} if archivo_env is not None else {}

    return Settings(
        APP_ENV=app_env,
        database=DatabaseSettings(**kwargs_env_file),
        redis=RedisSettings(**kwargs_env_file),
        minio=MinioSettings(**kwargs_env_file),
        playwright=PlaywrightSettings(**kwargs_env_file),
        scraping=ScrapingSettings(**kwargs_env_file),
        logging=LoggingSettings(**kwargs_env_file),
        api=ApiSettings(**kwargs_env_file),
    )


def reset_settings_cache() -> None:
    """Limpia la cache de settings. Uso exclusivo de tests."""
    get_settings.cache_clear()
