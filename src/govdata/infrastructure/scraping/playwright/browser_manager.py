"""BrowserManager: ciclo de vida y pool de contextos de Playwright.

Un `BrowserManager` lanza UN SOLO proceso de navegador (Chromium) y lo
reutiliza para toda su vida util ("reutilizacion del navegador"). Cada
unidad de trabajo (una entidad) recibe un `BrowserContext` nuevo y aislado
("pool de contextos"): esto evita que cookies/estado de una entidad
contaminen la siguiente, sin pagar el costo de lanzar un browser process
por entidad (lo caro de Playwright es el proceso del navegador, no el
contexto).

Nota de concurrencia: la Sync API de Playwright NO es thread-safe -- un
objeto `Playwright`/`Browser` solo puede usarse desde el hilo que lo creo.
Por eso `PipelineOrchestratorService` crea UN `BrowserManager` POR HILO
worker (ver ese modulo), nunca comparte uno entre hilos.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from types import TracebackType
from typing import Self

from playwright.sync_api import Browser, BrowserContext, Playwright, sync_playwright

from govdata.config.settings import PlaywrightSettings


class BrowserManager:
    """Administra un unico Browser Chromium y entrega contextos aislados."""

    def __init__(self, settings: PlaywrightSettings) -> None:
        self._settings = settings
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    def iniciar(self) -> None:
        if self._browser is not None:
            return
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self._settings.headless)

    def cerrar(self) -> None:
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    @contextmanager
    def nuevo_contexto(self) -> Iterator[BrowserContext]:
        """Entrega un `BrowserContext` nuevo (aislado) y lo cierra al salir.

        Lanza el navegador de forma perezosa en la primera llamada, para
        que crear un `BrowserManager` no implique abrir un proceso de
        Chromium si nunca se usa (util en tests que solo instancian el
        objeto sin ejecutar nada).
        """
        self.iniciar()
        assert self._browser is not None  # para mypy: iniciar() lo garantiza
        contexto = self._browser.new_context(user_agent=self._settings.user_agent)
        contexto.set_default_timeout(self._settings.timeout_ms)
        try:
            yield contexto
        finally:
            contexto.close()

    def __enter__(self) -> Self:
        self.iniciar()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.cerrar()
