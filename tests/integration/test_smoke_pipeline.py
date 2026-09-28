"""Smoke test funcional: pipeline de descubrimiento end-to-end.

Ejercita la cadena COMPLETA del Modulo 2 con componentes reales (Playwright
real contra el servidor de fixtures local, repositorios SQLAlchemy reales
contra SQLite en memoria) -- solo el portal remoto y PostgreSQL se
sustituyen por sus equivalentes locales/en-memoria para poder correr en
CI sin red ni infraestructura externa.
"""

from __future__ import annotations

from sqlalchemy.orm import sessionmaker

from govdata.application.ports.entidad_worker_port import EntidadWorkerPort
from govdata.application.services.pipeline_orchestrator_service import PipelineOrchestratorService
from govdata.application.use_cases.descubrir_documento_use_case import DescubrirDocumentoUseCase
from govdata.application.use_cases.descubrir_entidad_use_case import DescubrirEntidadUseCase
from govdata.application.use_cases.descubrir_ultima_publicacion_use_case import (
    DescubrirUltimaPublicacionUseCase,
)
from govdata.application.use_cases.listar_entidades_use_case import ListarEntidadesUseCase
from govdata.config.settings import PlaywrightSettings, ScrapingSettings
from govdata.domain.entities.entidad import Entidad
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_documento_repository import (
    SqlAlchemyDocumentoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_entidad_repository import (
    SqlAlchemyEntidadRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_publicacion_repository import (
    SqlAlchemyPublicacionRepository,
)
from govdata.infrastructure.scraping.dpe_entidad_worker import DpeEntidadWorker
from govdata.infrastructure.scraping.playwright.dpe_scraper_adapter import DpeScraperAdapter
from govdata.infrastructure.scraping.rate_limiter import RateLimiter


class _WorkerDePrueba(EntidadWorkerPort):
    """Worker real (adapter + casos de uso reales) pero con un contexto de
    navegador y una sesion de BD ya provistos por los fixtures del test,
    para no reimplementar el ciclo de vida completo del Container aqui."""

    def __init__(self, contexto_navegador, sesion, url_origen) -> None:
        self._adapter = DpeScraperAdapter(
            contexto=contexto_navegador,
            rate_limiter=RateLimiter(intervalo_minimo_segundos=0.0),
            url_origen=url_origen,
            max_reintentos=1,
            backoff_base_segundos=0.01,
        )
        self._sesion = sesion

    def procesar(self, entidad: Entidad):
        caso_uso = DescubrirEntidadUseCase(
            descubrir_publicacion=DescubrirUltimaPublicacionUseCase(
                scraper=self._adapter,
                publicacion_repository=SqlAlchemyPublicacionRepository(self._sesion),
                anio_actual_provider=lambda: 2026,
            ),
            descubrir_documento=DescubrirDocumentoUseCase(
                scraper=self._adapter,
                documento_repository=SqlAlchemyDocumentoRepository(self._sesion),
            ),
        )
        resultado = caso_uso.ejecutar(entidad)
        self._sesion.flush()
        return resultado

    def cerrar(self) -> None:
        pass


def test_pipeline_completo_descubre_entidad_publicacion_y_documento(
    contexto_navegador, servidor_fixtures_dpe, sesion
) -> None:
    # Paso 1: listar y persistir entidades (usa la fixture de establishment/list)
    adapter = DpeScraperAdapter(
        contexto=contexto_navegador,
        rate_limiter=RateLimiter(intervalo_minimo_segundos=0.0),
        url_origen=servidor_fixtures_dpe.url_origen,
    )
    entidades = ListarEntidadesUseCase(
        scraper=adapter, entidad_repository=SqlAlchemyEntidadRepository(sesion)
    ).ejecutar()
    sesion.flush()
    assert len(entidades) == 4

    unae = next(e for e in entidades if e.metadata_extra["identificador_portal"] == "1920")

    # Paso 2-6: descubrir publicacion + documento para esa entidad especifica
    worker = _WorkerDePrueba(contexto_navegador, sesion, servidor_fixtures_dpe.url_origen)
    resultado = worker.procesar(unae)

    assert resultado.exito is True
    assert resultado.publicacion is not None
    assert resultado.publicacion.mes_publicado.year == 2026
    assert resultado.publicacion.mes_publicado.month == 6
    assert resultado.documento is not None
    assert resultado.documento.tipo_archivo.value == "csv"
    assert resultado.documento.esta_descargado is False  # Modulo 2 nunca descarga


def test_pipeline_orchestrator_con_lote_mixto_de_entidades(
    sqlite_engine_multihilo, servidor_fixtures_dpe
) -> None:
    """Una entidad exitosa (1920, con item) + una sin el item de directorio
    (1358) -- el orquestador debe reportar 1 exito y 1 fallo, sin excepciones.

    Usa el `DpeEntidadWorker` REAL (no un doble): cada hilo propio lanza su
    PROPIO `BrowserManager`, exactamente como en produccion -- Playwright
    Sync API no permite compartir un BrowserContext creado en un hilo
    distinto (se verifico empiricamente). Usa `sqlite_engine_multihilo`
    (archivo, no ":memory:") porque este test SI ejercita hilos
    concurrentes reales -- ver el docstring de esa fixture.
    """
    Factory = sessionmaker(bind=sqlite_engine_multihilo, future=True)
    entidades = [
        Entidad(id=1, nombre="UNAE", url_transparencia=f"{servidor_fixtures_dpe.url_origen}/entidades/1920", portal_origen="dpe"),
        Entidad(id=2, nombre="EPUNEMI", url_transparencia=f"{servidor_fixtures_dpe.url_origen}/entidades/1358", portal_origen="dpe"),
    ]

    scraping_settings = ScrapingSettings(
        url_origen_dpe=servidor_fixtures_dpe.url_origen,
        max_reintentos=1,
        backoff_base_segundos=0.01,
        intervalo_minimo_segundos=0.0,
    )
    rate_limiter = RateLimiter(intervalo_minimo_segundos=0.0)

    servicio = PipelineOrchestratorService(
        worker_factory=lambda: DpeEntidadWorker(
            session_factory=Factory,
            playwright_settings=PlaywrightSettings(headless=True),
            scraping_settings=scraping_settings,
            rate_limiter=rate_limiter,
        ),
        concurrencia_maxima=2,
    )
    resumen = servicio.ejecutar(entidades)

    assert resumen.total_entidades == 2
    assert resumen.documentos_encontrados == 1
    assert resumen.errores == 1
