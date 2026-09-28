"""Tests de integracion: BrowserManager (pool de contextos, reutilizacion)."""

from __future__ import annotations

from govdata.config.settings import PlaywrightSettings
from govdata.infrastructure.scraping.playwright.browser_manager import BrowserManager


def test_lanza_el_navegador_de_forma_perezosa() -> None:
    manager = BrowserManager(PlaywrightSettings(headless=True))
    assert manager._browser is None  # nunca se uso -> nunca se lanzo
    manager.cerrar()  # no debe lanzar aunque nunca se inicio


def test_reutiliza_el_mismo_browser_entre_contextos() -> None:
    manager = BrowserManager(PlaywrightSettings(headless=True))
    try:
        with manager.nuevo_contexto():
            browser_primera_vez = manager._browser
        with manager.nuevo_contexto():
            browser_segunda_vez = manager._browser

        assert browser_primera_vez is browser_segunda_vez
    finally:
        manager.cerrar()


def test_contextos_son_aislados_entre_si() -> None:
    manager = BrowserManager(PlaywrightSettings(headless=True))
    try:
        with manager.nuevo_contexto() as contexto_1:
            contexto_1.add_cookies(
                [{"name": "prueba", "value": "1", "url": "https://example.com"}]
            )
            cookies_ctx1 = contexto_1.cookies("https://example.com")

        with manager.nuevo_contexto() as contexto_2:
            cookies_ctx2 = contexto_2.cookies("https://example.com")

        assert len(cookies_ctx1) == 1
        assert len(cookies_ctx2) == 0  # el contexto nuevo no hereda cookies del anterior
    finally:
        manager.cerrar()


def test_context_manager_cierra_al_salir() -> None:
    with BrowserManager(PlaywrightSettings(headless=True)) as manager:
        assert manager._browser is not None
    # Tras salir del `with`, el browser debe estar cerrado.
    assert manager._browser is None
