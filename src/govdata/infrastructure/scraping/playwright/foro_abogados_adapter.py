"""Adaptador Playwright para el Foro de Abogados de la Función Judicial.

Implementa `ForoAbogadosPort` usando Playwright para interactuar con la
página real del Foro de Abogados, como lo haría una persona manualmente:

    1. Abrir la página del Foro de Abogados
    2. Llenar el campo CEDULA
    3. Hacer clic en el botón "Aceptar"
    4. Esperar a que cargue la respuesta
    5. Extraer la información del abogado

Los selectores están centralizados en `foro_abogados_selectors.py`.

Si la página muestra un CAPTCHA o challenge, se devuelve un estado controlado
`SOURCE_UNAVAILABLE` y NO se intenta resolver o evadir el CAPTCHA.
"""

from __future__ import annotations

from dataclasses import dataclass

from playwright.async_api import async_playwright

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.ports.foro_abogados_port import ForoAbogadosPort
from govdata.config.logging_config import get_logger
from govdata.domain.exceptions.domain_exceptions import GovDataError
from govdata.infrastructure.scraping.playwright.selectors import foro_abogados_selectors
from govdata.shared.security.redaccion_datos_personales import sanitizar_error_externo

logger = get_logger(__name__)


class FuenteForoNoDisponibleError(GovDataError):
    """La fuente no pudo ser consultada sin intentar evadir sus controles."""


@dataclass(frozen=True, slots=True)
class SelectoresForoAbogados:
    """Selectores centralizados para el Foro de Abogados."""

    input_cedula: str = foro_abogados_selectors.SELECTOR_INPUT_CEDULA
    boton_ceptar: str = foro_abogados_selectors.SELECTOR_BOTON_ACEPTAR
    tabla_resultados: str = foro_abogados_selectors.SELECTOR_TABLA_RESULTADOS
    filas_resultados: str = foro_abogados_selectors.SELECTOR_FILAS_RESULTADOS


class ForoAbogadosPlaywrightAdapter(ForoAbogadosPort):
    """Adaptador Playwright para el Foro de Abogados de la Función Judicial."""

    def __init__(
        self,
        selectores: SelectoresForoAbogados | None = None,
        timeout_ms: int = 30_000,
        headless: bool = True,
    ) -> None:
        self._selectores = selectores or SelectoresForoAbogados()
        self._timeout_ms = timeout_ms
        self._headless = headless

    def buscar_por_cedula(self, cedula: str) -> list[RegistroForoDTO]:
        """Busca un abogado por cédula en el Foro de Abogados.

        La cédula es únicamente una llave técnica transitoria: se usa para
        consultar el registro profesional, pero nunca se almacena en logs,
        respuestas de API, ni exportaciones.
        """
        import asyncio

        return asyncio.run(self._buscar_por_cedula_async(cedula))

    async def _buscar_por_cedula_async(self, cedula: str) -> list[RegistroForoDTO]:
        """Implementación asíncrona de la búsqueda por cédula."""
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=self._headless)
                try:
                    page = await browser.new_page()
                    page.set_default_timeout(self._timeout_ms)

                    # 1. Abrir la página del Foro de Abogados
                    await page.goto(
                        foro_abogados_selectors.URL_CONSULTA,
                        wait_until="domcontentloaded",
                    )

                    # Verificar si hay CAPTCHA o challenge
                    contenido = await page.content()
                    if self._detectar_captcha(contenido):
                        logger.warning("foro_captcha_detectado")
                        raise FuenteForoNoDisponibleError(
                            "SOURCE_UNAVAILABLE: CAPTCHA detectado en el Foro de Abogados"
                        )

                    # 2. Llenar el campo CEDULA
                    await page.fill(self._selectores.input_cedula, cedula)

                    # 3. Hacer clic en el botón "Aceptar"
                    await page.click(self._selectores.boton_ceptar)

                    # 4. Esperar a que cargue la respuesta
                    await page.wait_for_load_state("networkidle")

                    # Verificar si hay CAPTCHA después del envío
                    contenido = await page.content()
                    if self._detectar_captcha(contenido):
                        logger.warning("foro_captcha_detectado")
                        raise FuenteForoNoDisponibleError(
                            "SOURCE_UNAVAILABLE: CAPTCHA detectado en el Foro de Abogados"
                        )

                    # 5. Extraer la información del abogado
                    registros = await self._extraer_registros(page)

                    logger.info(
                        "foro_consulta_exitosa",
                        registros=len(registros),
                    )
                    return registros

                finally:
                    await browser.close()
        except FuenteForoNoDisponibleError:
            raise
        except Exception as exc:
            error_seguro = sanitizar_error_externo(exc)
            logger.error("foro_error", error=error_seguro)
            raise FuenteForoNoDisponibleError(
                f"SOURCE_UNAVAILABLE: error al consultar el Foro de Abogados: {error_seguro}"
            ) from exc

    async def _extraer_registros(self, page) -> list[RegistroForoDTO]:
        """Extrae los registros de la página de resultados."""
        registros: list[RegistroForoDTO] = []

        # Verificar si hay resultados
        tabla = await page.query_selector(self._selectores.tabla_resultados)
        if tabla is None:
            logger.info("foro_sin_resultados")
            return registros

        # Extraer filas de la tabla
        filas = await page.query_selector_all(self._selectores.filas_resultados)
        for fila in filas:
            celdas = await fila.query_selector_all("td")
            if len(celdas) < 2:
                continue

            # Extraer información de las celdas (la estructura puede variar)
            valores = [await celda.text_content() for celda in celdas]
            valores = [v.strip() if v else "" for v in valores]

            # Crear un RegistroForoDTO con la información disponible
            # (la estructura exacta de la respuesta puede variar)
            registros.append(
                RegistroForoDTO(
                    nombre_completo=valores[0] if valores else None,
                    registro=valores[1] if len(valores) > 1 else None,
                )
            )

        return registros

    def _detectar_captcha(self, contenido: str) -> bool:
        """Detecta si la página contiene un CAPTCHA o challenge."""
        contenido_lower = contenido.lower()
        return any(
            palabra in contenido_lower
            for palabra in ("captcha", "recaptcha", "g-recaptcha", "challenge", "just a moment")
        )

    # Los métodos buscar_por_persona y buscar_por_persona_master no son
    # aplicables aquí porque el Foro de Abogados solo permite búsqueda por
    # cédula, no por nombre. Se lanzan errores informativos.
    def buscar_por_persona(self, persona) -> list[RegistroForoDTO]:
        raise FuenteForoNoDisponibleError(
            "SOURCE_UNAVAILABLE: el Foro de Abogados solo permite búsqueda por cédula"
        )

    def buscar_por_persona_master(self, persona_master) -> list[RegistroForoDTO]:
        raise FuenteForoNoDisponibleError(
            "SOURCE_UNAVAILABLE: el Foro de Abogados solo permite búsqueda por cédula"
        )
