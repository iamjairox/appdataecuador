"""Adaptador Playwright para EcuadorLegalOnline - Tercera opción de consulta de cédula.

Implementa `ConsultaCedulaPort` usando Playwright para interactuar con la
página de EcuadorLegalOnline, como lo haría una persona manualmente:

    1. Abrir la página de consulta
    2. Llenar el formulario con apellidos y nombres
    3. Hacer clic en el botón "Consultar"
    4. Extraer los resultados

Los selectores están centralizados en `ecuadorlegalonline_selectors.py`.

Nunca se selecciona automáticamente el primer resultado: el motor de
matching (`matching_cedula.py`) es el que decide cuál candidato es el
correcto, o si hay ambigüedad.
"""

from __future__ import annotations

from dataclasses import dataclass

from playwright.async_api import async_playwright

from govdata.application.dto.identificacion_cedula_dto import CedulaCandidateDTO
from govdata.application.ports.consulta_cedula_port import ConsultaCedulaPort
from govdata.config.settings import get_settings
from govdata.config.logging_config import get_logger
from govdata.domain.exceptions.domain_exceptions import FuenteCedulaNoDisponibleError
from govdata.domain.rules.matching_cedula import candidato_desde_fila_fuente
from govdata.infrastructure.scraping.playwright.bloqueo_antibot import pagina_bloqueada_por_antibot
from govdata.infrastructure.scraping.playwright.selectors import ecuadorlegalonline_selectors
from govdata.shared.security.redaccion_datos_personales import sanitizar_error_externo

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SelectoresEcuadorLegalOnline:
    """Selectores centralizados para EcuadorLegalOnline."""

    input_nombre: str = ecuadorlegalonline_selectors.SELECTOR_INPUT_NOMBRE
    boton_consultar: str = ecuadorlegalonline_selectors.SELECTOR_BOTON_CONSULTAR
    resultado: str = ecuadorlegalonline_selectors.SELECTOR_RESULTADO
    tabla_resultados: str = ecuadorlegalonline_selectors.SELECTOR_TABLA_RESULTADOS
    filas_resultados: str = ecuadorlegalonline_selectors.SELECTOR_FILAS_RESULTADOS
    cedula: str = ecuadorlegalonline_selectors.SELECTOR_CEDULA
    nombre_completo: str = ecuadorlegalonline_selectors.SELECTOR_NOMBRE_COMPLETO


class EcuadorLegalOnlineAdapter(ConsultaCedulaPort):
    """Adaptador Playwright para EcuadorLegalOnline."""

    def __init__(
        self,
        selectores: SelectoresEcuadorLegalOnline | None = None,
        timeout_ms: int = 30_000,
        headless: bool = True,
    ) -> None:
        self._selectores = selectores or SelectoresEcuadorLegalOnline()
        self._timeout_ms = timeout_ms
        self._headless = headless

    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]:
        """Consulta EcuadorLegalOnline con los nombres y apellidos dados.

        Nunca selecciona automáticamente el primer resultado: devuelve todos
        los candidatos encontrados para que el motor de matching decida.
        """
        # El formato es "Apellidos Nombres"
        nombre_completo = f"{apellido_paterno} {apellido_materno} {nombres}".strip()

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=self._headless)
                try:
                    page = await browser.new_page()
                    page.set_default_timeout(self._timeout_ms)

                    # 1. Abrir la página de consulta
                    await page.goto(
                        ecuadorlegalonline_selectors.URL_CONSULTA,
                        wait_until="domcontentloaded",
                    )

                    # Verificar si hay CAPTCHA o challenge
                    contenido = await page.content()
                    if get_settings().scraping.rechazar_captcha_antibot and self._detectar_captcha(contenido):
                        logger.warning("ecuadorlegalonline_captcha_detectado")
                        raise FuenteCedulaNoDisponibleError(
                            "SOURCE_UNAVAILABLE: CAPTCHA detectado en EcuadorLegalOnline"
                        )

                    # 2. Llenar el formulario
                    await page.fill(self._selectores.input_nombre, nombre_completo)

                    # 3. Hacer clic en el botón "Consultar"
                    await page.click(self._selectores.boton_consultar)

                    # 4. Esperar a que carguen los resultados
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(2000)

                    # Verificar si hay CAPTCHA después del envío
                    contenido = await page.content()
                    if get_settings().scraping.rechazar_captcha_antibot and self._detectar_captcha(contenido):
                        logger.warning("ecuadorlegalonline_captcha_detectado")
                        raise FuenteCedulaNoDisponibleError(
                            "SOURCE_UNAVAILABLE: CAPTCHA detectado en EcuadorLegalOnline"
                        )

                    # 5. Extraer los resultados
                    candidatos = await self._extraer_candidatos(page)

                    logger.info(
                        "ecuadorlegalonline_consulta_exitosa",
                        candidatos=len(candidatos),
                    )
                    return candidatos

                finally:
                    await browser.close()
        except FuenteCedulaNoDisponibleError:
            raise
        except Exception as exc:
            error_seguro = sanitizar_error_externo(exc)
            logger.error("ecuadorlegalonline_error", error=error_seguro)
            raise FuenteCedulaNoDisponibleError(
                f"SOURCE_UNAVAILABLE: error al consultar EcuadorLegalOnline: {error_seguro}"
            ) from exc

    async def _extraer_candidatos(self, page) -> list[CedulaCandidateDTO]:
        """Extrae los candidatos de la tabla de resultados."""
        candidatos: list[CedulaCandidateDTO] = []

        # Verificar si hay resultados
        resultado = await page.query_selector(self._selectores.resultado)
        if resultado is None:
            logger.info("ecuadorlegalonline_sin_resultados")
            return candidatos

        # Verificar si hay una tabla de resultados
        tabla = await page.query_selector(self._selectores.tabla_resultados)
        if tabla is None:
            logger.info("ecuadorlegalonline_sin_tabla_resultados")
            return candidatos

        filas = await page.query_selector_all(self._selectores.filas_resultados)
        if not filas:
            filas = await page.query_selector_all("#resultado table tr, table tr")
        for fila in filas:
            cedula = await fila.query_selector(self._selectores.cedula)
            nombre = await fila.query_selector(self._selectores.nombre_completo)

            if cedula is None or nombre is None:
                continue

            candidato = candidato_desde_fila_fuente(
                await cedula.text_content() or "",
                await nombre.text_content() or "",
            )
            if candidato is not None:
                candidatos.append(candidato)

        return candidatos

    def _detectar_captcha(self, contenido: str) -> bool:
        return pagina_bloqueada_por_antibot(contenido)
