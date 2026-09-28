"""Adaptador: DpeEntidadWorker.

Implementacion de `EntidadWorkerPort` para el portal DPE. Es propietario
de recursos costosos reutilizables entre entidades procesadas por el
mismo hilo:

    - Un `BrowserManager` (un solo proceso Chromium, lanzado de forma
      perezosa en el primer `procesar()`).
    - El `RateLimiter` (compartido entre TODOS los workers/hilos -- se
      inyecta, nunca se crea uno por worker, porque el limite es sobre el
      portal como un todo).

Por cada entidad procesada abre un `BrowserContext` nuevo (pool de
contextos, aislamiento entre entidades) y una sesion de base de datos
nueva (Unit of Work por entidad: si algo falla a mitad de camino, no dejar
datos a medias de esa entidad, pero tampoco afectar a las demas).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from govdata.application.dto.resultado_descubrimiento_dto import ResultadoDescubrimientoEntidadDTO
from govdata.application.ports.entidad_worker_port import EntidadWorkerPort
from govdata.application.use_cases.descubrir_documento_use_case import DescubrirDocumentoUseCase
from govdata.application.use_cases.descubrir_entidad_use_case import DescubrirEntidadUseCase
from govdata.application.use_cases.descubrir_ultima_publicacion_use_case import (
    DescubrirUltimaPublicacionUseCase,
)
from govdata.config.logging_config import get_logger
from govdata.config.settings import PlaywrightSettings, ScrapingSettings
from govdata.domain.entities.ejecucion import Ejecucion, EstadoEjecucion
from govdata.domain.entities.entidad import Entidad
from govdata.infrastructure.persistence.postgresql.database import sesion_scope
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_documento_repository import (
    SqlAlchemyDocumentoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_ejecucion_repository import (
    SqlAlchemyEjecucionRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_publicacion_repository import (
    SqlAlchemyPublicacionRepository,
)
from govdata.infrastructure.scraping.playwright.browser_manager import BrowserManager
from govdata.infrastructure.scraping.playwright.dpe_scraper_adapter import DpeScraperAdapter
from govdata.infrastructure.scraping.rate_limiter import RateLimiter

logger = get_logger(__name__)

_ETAPA_DESCUBRIMIENTO = "descubrimiento"


class DpeEntidadWorker(EntidadWorkerPort):
    """Worker de descubrimiento DPE: un navegador reutilizado, N entidades."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        playwright_settings: PlaywrightSettings,
        scraping_settings: ScrapingSettings,
        rate_limiter: RateLimiter,
    ) -> None:
        self._session_factory = session_factory
        self._scraping_settings = scraping_settings
        self._rate_limiter = rate_limiter
        self._browser_manager = BrowserManager(playwright_settings)

    def procesar(self, entidad: Entidad) -> ResultadoDescubrimientoEntidadDTO:
        iniciado_en = datetime.now(UTC)
        with self._browser_manager.nuevo_contexto() as contexto:
            adapter = DpeScraperAdapter(
                contexto=contexto,
                rate_limiter=self._rate_limiter,
                url_origen=self._scraping_settings.url_origen_dpe,
                max_reintentos=self._scraping_settings.max_reintentos,
                backoff_base_segundos=self._scraping_settings.backoff_base_segundos,
            )
            with sesion_scope(self._session_factory) as sesion:
                caso_uso = DescubrirEntidadUseCase(
                    descubrir_publicacion=DescubrirUltimaPublicacionUseCase(
                        scraper=adapter,
                        publicacion_repository=SqlAlchemyPublicacionRepository(sesion),
                        anios_lookback_maximo=self._scraping_settings.anios_lookback_maximo,
                    ),
                    descubrir_documento=DescubrirDocumentoUseCase(
                        scraper=adapter,
                        documento_repository=SqlAlchemyDocumentoRepository(sesion),
                        umbral_confianza_item=self._scraping_settings.umbral_confianza_item,
                        umbral_confianza_archivo=self._scraping_settings.umbral_confianza_archivo,
                    ),
                )
                resultado = caso_uso.ejecutar(entidad)

                finalizado_en = datetime.now(UTC)
                SqlAlchemyEjecucionRepository(sesion).registrar(
                    Ejecucion(
                        entidad_id=entidad.id,
                        etapa=_ETAPA_DESCUBRIMIENTO,
                        estado=EstadoEjecucion.EXITO if resultado.exito else EstadoEjecucion.FALLO,
                        mensaje_error=resultado.error,
                        iniciado_en=iniciado_en,
                        finalizado_en=finalizado_en,
                    )
                )
                return resultado

    def cerrar(self) -> None:
        self._browser_manager.cerrar()
