"""Adaptador Async Playwright de Consultas Ecuador.

No contiene selectores inferidos.  La automatización queda deshabilitada hasta
que una inspección autorizada del DOM proporcione el mapa de controles.
"""

from __future__ import annotations

from dataclasses import dataclass

from govdata.config.settings import get_settings

from playwright.async_api import async_playwright

from govdata.application.dto.identificacion_cedula_dto import CedulaCandidateDTO
from govdata.application.ports.consulta_cedula_port import ConsultaCedulaPort
from govdata.domain.exceptions.domain_exceptions import FuenteCedulaNoDisponibleError


@dataclass(frozen=True, slots=True)
class SelectoresConsultaEcuador:
    apellidos: str | None = None
    nombres: str | None = None
    consultar: str | None = None
    filas_resultado: str | None = None


class ConsultaEcuadorAsyncAdapter(ConsultaCedulaPort):
    url = "https://consultasecuador.com/en-linea/personas/consultar-cedula-con-nombres"

    def __init__(self, selectores: SelectoresConsultaEcuador, timeout_ms: int = 30_000) -> None:
        self._selectores = selectores
        self._timeout_ms = timeout_ms

    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]:
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                try:
                    page = await browser.new_page()
                    page.set_default_timeout(self._timeout_ms)
                    await page.goto(self.url, wait_until="domcontentloaded")
                    contenido = (await page.content()).lower()
                    if get_settings().scraping.rechazar_captcha_antibot and (
                        "just a moment" in contenido or "challenge" in contenido or "captcha" in contenido
                    ):
                        raise FuenteCedulaNoDisponibleError("SOURCE_UNAVAILABLE: challenge anti-bot de Consultas Ecuador")
                    if not all((self._selectores.apellidos, self._selectores.nombres, self._selectores.consultar, self._selectores.filas_resultado)):
                        raise FuenteCedulaNoDisponibleError("SOURCE_UNAVAILABLE: selectores reales aún no aprobados")
                    # La extracción se habilita solo con selectores inspeccionados y revisados.
                    raise FuenteCedulaNoDisponibleError("SOURCE_UNAVAILABLE: extractor pendiente de mapa DOM aprobado")
                finally:
                    await browser.close()
        except FuenteCedulaNoDisponibleError:
            raise
        except Exception as exc:
            raise FuenteCedulaNoDisponibleError("SOURCE_UNAVAILABLE: error al abrir Consultas Ecuador") from exc
