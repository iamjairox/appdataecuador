"""Adaptador Playwright para ConsultaEcuador - Segunda opción de consulta de cédula.

Implementa `ConsultaCedulaPort` usando Playwright para interactuar con la
página de ConsultaEcuador, como lo haría una persona manualmente:

    1. Abrir la página de consulta
    2. Llenar el formulario con apellidos y nombres
    3. Enviar el formulario
    4. Extraer los resultados de la tabla

Los selectores están centralizados en `consultasecuador_selectors.py`.

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
from govdata.infrastructure.scraping.playwright.selectors import consultasecuador_selectors
from govdata.shared.security.redaccion_datos_personales import sanitizar_error_externo

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SelectoresConsultaEcuador:
    """Selectores centralizados para ConsultaEcuador."""

    input_apellidos: str = consultasecuador_selectors.SELECTOR_INPUT_APELLIDOS
    input_nombres: str = consultasecuador_selectors.SELECTOR_INPUT_NOMBRES
    boton_consultar: str = consultasecuador_selectors.SELECTOR_BOTON_CONSULTAR
    tabla_resultados: str = consultasecuador_selectors.SELECTOR_TABLA_RESULTADOS
    filas_resultados: str = consultasecuador_selectors.SELECTOR_FILAS_RESULTADOS
    cedula: str = consultasecuador_selectors.SELECTOR_CEDULA
    nombre_completo: str = consultasecuador_selectors.SELECTOR_NOMBRE_COMPLETO


class ConsultaEcuadorAdapter(ConsultaCedulaPort):
    """Adaptador Playwright para ConsultaEcuador."""

    def __init__(
        self,
        selectores: SelectoresConsultaEcuador | None = None,
        timeout_ms: int = 30_000,
        headless: bool = True,
    ) -> None:
        self._selectores = selectores or SelectoresConsultaEcuador()
        self._timeout_ms = timeout_ms
        self._headless = headless

    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]:
        """Consulta ConsultaEcuador con los nombres y apellidos dados.

        Nunca selecciona automáticamente el primer resultado: devuelve todos
        los candidatos encontrados para que el motor de matching decida.
        """
        apellidos = f"{apellido_paterno} {apellido_materno}".strip()

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=self._headless)
                try:
                    page = await browser.new_page()
                    page.set_default_timeout(self._timeout_ms)

                    # 1. Abrir la página de consulta
                    await page.goto(
                        consultasecuador_selectors.URL_CONSULTA,
                        wait_until="domcontentloaded",
                    )

                    # Verificar si hay CAPTCHA o challenge
                    contenido = await page.content()
                    if get_settings().scraping.rechazar_captcha_antibot and self._detectar_captcha(contenido):
                        logger.warning("consultasecuador_captcha_detectado")
                        raise FuenteCedulaNoDisponibleError(
                            "SOURCE_UNAVAILABLE: CAPTCHA detectado en ConsultaEcuador"
                        )

                    # 2. Llenar el formulario
                    await page.fill(self._selectores.input_apellidos, apellidos)
                    await page.fill(self._selectores.input_nombres, nombres)

                    # 3. Enviar el formulario
                    await page.click(self._selectores.boton_consultar)

                    # 4. Esperar a que carguen los resultados
                    await page.wait_for_load_state("networkidle")

                    # Verificar si hay CAPTCHA después del envío
                    contenido = await page.content()
                    if get_settings().scraping.rechazar_captcha_antibot and self._detectar_captcha(contenido):
                        logger.warning("consultasecuador_captcha_detectado")
                        raise FuenteCedulaNoDisponibleError(
                            "SOURCE_UNAVAILABLE: CAPTCHA detectado en ConsultaEcuador"
                        )

                    # 5. Extraer los resultados de la tabla
                    candidatos = await self._extraer_candidatos(page)

                    logger.info(
                        "consultasecuador_consulta_exitosa",
                        candidatos=len(candidatos),
                    )
                    return candidatos

                finally:
                    await browser.close()
        except FuenteCedulaNoDisponibleError:
            raise
        except Exception as exc:
            error_seguro = sanitizar_error_externo(exc)
            logger.error("consultasecuador_error", error=error_seguro)
            raise FuenteCedulaNoDisponibleError(
                f"SOURCE_UNAVAILABLE: error al consultar ConsultaEcuador: {error_seguro}"
            ) from exc

    async def _extraer_candidatos(self, page) -> list[CedulaCandidateDTO]:
        """Extrae los candidatos de la tabla de resultados."""
        candidatos: list[CedulaCandidateDTO] = []

        # Verificar si hay resultados
        tabla = await page.query_selector(self._selectores.tabla_resultados)
        if tabla is None:
            logger.info("consultasecuador_sin_resultados")
            return candidatos

        filas = await page.query_selector_all(self._selectores.filas_resultados)
        if not filas:
            filas = await page.query_selector_all("table tr")
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
