"""Adaptador Playwright para SENESCYT -- primera opcion de consulta de cedula.

Implementa `ConsultaCedulaPort` usando Playwright para interactuar con la
pagina real de consulta de titulos (MINEDEC/SENESCYT), como lo haria una
persona manualmente:

    1. Abrir la pagina de consulta (solo se ingresan los apellidos)
    2. Llenar el campo de apellidos ("paterno materno")
    3. Hacer clic en el boton "Buscar"
    4. Extraer los candidatos (cedula + nombre) de la tabla de resultados

Los selectores estan centralizados en `senescyt_selectors.py`.

Tampoco selecciona automaticamente el primer resultado: devuelve todos
los candidatos para que el motor de matching decida.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from playwright.async_api import Page, async_playwright

from govdata.application.dto.identificacion_cedula_dto import CedulaCandidateDTO
from govdata.application.ports.consulta_cedula_port import ConsultaCedulaPort
from govdata.config.logging_config import get_logger
from govdata.config.settings import get_settings
from govdata.domain.exceptions.domain_exceptions import GovDataError
from govdata.infrastructure.scraping.playwright.selectors import senescyt_selectors
from govdata.shared.security.redaccion_datos_personales import sanitizar_error_externo

logger = get_logger(__name__)

_PATRON_CEDULA = re.compile(r"^\d{10}$")


class FuenteCedulaNoDisponibleError(GovDataError):
    """La fuente no esta disponible para la consulta."""


@dataclass(frozen=True, slots=True)
class SelectoresSenescyt:
    """Selectores centralizados para SENESCYT."""

    input_apellidos: str = senescyt_selectors.SELECTOR_INPUT_APELLIDOS
    boton_buscar: str = senescyt_selectors.SELECTOR_BOTON_BUSCAR
    captcha_img: str = senescyt_selectors.SELECTOR_CAPTCHA_IMG
    captcha_input: str = senescyt_selectors.SELECTOR_CAPTCHA_INPUT
    tabla_resultados: str = senescyt_selectors.SELECTOR_TABLA_RESULTADOS
    filas_resultados: str = senescyt_selectors.SELECTOR_FILAS_RESULTADOS


class SenescytCedulaAdapter(ConsultaCedulaPort):
    """Adaptador Playwright para SENESCYT (busqueda por apellidos)."""

    def __init__(
        self,
        selectores: SelectoresSenescyt | None = None,
        timeout_ms: int = 30_000,
        headless: bool = True,
    ) -> None:
        self._selectores = selectores or SelectoresSenescyt()
        self._timeout_ms = timeout_ms
        self._headless = headless

    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]:
        """Consulta SENESCYT solo con apellidos ("paterno materno").

        Nunca selecciona automaticamente el primer resultado: devuelve todos
        los candidatos encontrados para que el motor de matching decida.
        """
        apellidos = f"{apellido_paterno} {apellido_materno}".strip()

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=self._headless)
                try:
                    page = await browser.new_page()
                    page.set_default_timeout(self._timeout_ms)

                    # 1. Abrir la pagina de consulta
                    await page.goto(
                        senescyt_selectors.URL_CONSULTA,
                        wait_until="domcontentloaded",
                    )

                    # 2. Detectar si la pagina requiere captcha de imagen.
                    if get_settings().scraping.rechazar_captcha_antibot and await self._tiene_captcha(page):
                        logger.warning("senescyt_captcha_requerido")
                        raise FuenteCedulaNoDisponibleError(
                            "SOURCE_UNAVAILABLE: SENESCYT exige captcha de imagen"
                        )

                    # 3. Llenar solo el campo de apellidos
                    await page.fill(self._selectores.input_apellidos, apellidos)

                    # 4. El boton Buscar nace `disabled` y solo se habilita al
                    # resolver el captcha de imagen. Si sigue deshabilitado,
                    # NO se intenta nada mas: estado controlado y fallback.
                    boton = await page.query_selector(self._selectores.boton_buscar)
                    if boton is None or not await boton.is_enabled():
                        logger.warning("senescyt_boton_bloqueado_por_captcha")
                        raise FuenteCedulaNoDisponibleError(
                            "SOURCE_UNAVAILABLE: SENESCYT exige captcha de imagen"
                        )

                    # 5. Hacer clic en Buscar y esperar la respuesta
                    await boton.click()
                    await page.wait_for_load_state("networkidle")

                    # 6. El servidor puede pedir captcha tras el envio
                    if await self._tiene_captcha(page):
                        logger.warning("senescyt_captcha_requerido_post_envio")
                        raise FuenteCedulaNoDisponibleError(
                            "SOURCE_UNAVAILABLE: SENESCYT exige captcha de imagen"
                        )

                    # 7. Extraer los candidatos de la tabla de resultados
                    candidatos = await self._extraer_candidatos(page)

                    logger.info(
                        "senescyt_consulta_exitosa",
                        candidatos=len(candidatos),
                    )
                    return candidatos

                finally:
                    await browser.close()
        except FuenteCedulaNoDisponibleError:
            raise
        except Exception as exc:
            error_seguro = sanitizar_error_externo(exc)
            logger.error("senescyt_cedula_error", error=error_seguro)
            raise FuenteCedulaNoDisponibleError(
                f"SOURCE_UNAVAILABLE: error al consultar SENESCYT: {error_seguro}"
            ) from exc

    async def _tiene_captcha(self, page: Page) -> bool:
        """Detecta el captcha de imagen o su campo, y captchas genericos."""
        if await page.query_selector(self._selectores.captcha_img) is not None:
            return True
        if await page.query_selector(self._selectores.captcha_input) is not None:
            return True
        contenido = (await page.content()).lower()
        return any(
            palabra in contenido
            for palabra in ("captcha", "recaptcha", "g-recaptcha", "just a moment")
        )

    async def _extraer_candidatos(self, page: Page) -> list[CedulaCandidateDTO]:
        """Extrae candidatos de la tabla de resultados.

        Estructura confirmada (captura real 2026-10-03):
        `Identificacion | Nombres y Apellidos | Opciones`, ej.
        `0703406181 | ZAMBRANO TINOCO ZULLY MARIA | Ver Informacion`.

        El parser prefiere esa estructura por posicion (col 1 = cedula,
        col 2 = nombre) y conserva un modo tolerante por si el sitio
        cambia el orden de columnas.
        """
        candidatos: list[CedulaCandidateDTO] = []

        filas = await page.query_selector_all(self._selectores.filas_resultados)
        if not filas:
            filas = await page.query_selector_all("tr")
        for fila in filas:
            celdas = await fila.query_selector_all("td, th")
            textos = [((await c.text_content()) or "").strip() for c in celdas]
            textos = [t for t in textos if t]
            if not textos:
                continue

            cedula: str | None = None
            nombre_texto: str | None = None
            # Modo exacto: [cedula, nombre, ...] por posicion.
            if len(textos) >= 2 and _PATRON_CEDULA.match(textos[0]):
                cedula = textos[0]
                nombre_texto = textos[1]
            else:
                # Modo tolerante: primera celda de 10 digitos + texto
                # alfabetico mas largo de la misma fila.
                cedula = next((t for t in textos if _PATRON_CEDULA.match(t)), None)
                if cedula is None:
                    continue
                resto = [t for t in textos if t != cedula and any(ch.isalpha() for ch in t)]
                if not resto:
                    continue
                nombre_texto = max(resto, key=len)

            partes = nombre_texto.split()
            if len(partes) >= 3:
                apellidos = " ".join(partes[:2])
                nombres = " ".join(partes[2:])
            elif len(partes) == 2:
                apellidos = partes[0]
                nombres = partes[1]
            else:
                apellidos = ""
                nombres = nombre_texto

            candidatos.append(
                CedulaCandidateDTO(
                    cedula=cedula,
                    nombres=nombres,
                    apellido_paterno=apellidos,
                )
            )

        if not candidatos:
            logger.info("senescyt_sin_resultados")
        return candidatos
