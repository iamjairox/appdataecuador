"""Adaptador Playwright para SRI - Consulta de cédula por apellidos y nombres.

Implementa `ConsultaCedulaPort` usando Playwright para interactuar con la
página real de SRI, como lo haría una persona manualmente:

    1. Abrir la página de consulta de deudas
    2. Hacer clic en "Continuar Navegando" si aparece
    3. Seleccionar la pestaña "Apellidos y nombres"
    4. Llenar el campo con "APELLIDOS NOMBRES"
    5. Hacer clic en "Consultar"
    6. Extraer la cédula de la tabla de resultados

Los selectores están centralizados en `sri_selectors.py`.

Nunca se selecciona automáticamente el primer resultado: el motor de
matching (`matching_cedula.py`) es el que decide cuál candidato es el
correcto, o si hay ambigüedad.
"""

from __future__ import annotations

from dataclasses import dataclass

from playwright.async_api import Page, async_playwright

from govdata.application.dto.identificacion_cedula_dto import CedulaCandidateDTO
from govdata.application.ports.consulta_cedula_port import ConsultaCedulaPort
from govdata.config.logging_config import get_logger
from govdata.domain.exceptions.domain_exceptions import GovDataError
from govdata.infrastructure.scraping.playwright.selectors import sri_selectors
from govdata.shared.security.redaccion_datos_personales import sanitizar_error_externo

logger = get_logger(__name__)


class FuenteCedulaNoDisponibleError(GovDataError):
    """La fuente no pudo ser consultada sin intentar evadir sus controles."""


@dataclass(frozen=True, slots=True)
class SelectoresSRI:
    """Selectores centralizados para SRI."""

    input_apellidos_nombres: str = sri_selectors.SELECTOR_INPUT_APELLIDOS_NOMBRES
    boton_consultar: str = sri_selectors.SELECTOR_BOTON_CONSULTAR
    tabla_resultados: str = sri_selectors.SELECTOR_TABLA_RESULTADOS
    filas_resultados: str = sri_selectors.SELECTOR_FILAS_RESULTADOS
    cedula: str = sri_selectors.SELECTOR_CEDULA
    nombre: str = sri_selectors.SELECTOR_NOMBRE


class SRIAdapter(ConsultaCedulaPort):
    """Adaptador Playwright para SRI (consulta por apellidos y nombres)."""

    def __init__(
        self,
        selectores: SelectoresSRI | None = None,
        timeout_ms: int = 30_000,
        headless: bool = True,
    ) -> None:
        self._selectores = selectores or SelectoresSRI()
        self._timeout_ms = timeout_ms
        self._headless = headless

    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]:
        """Consulta SRI con los apellidos y nombres dados.

        Nunca selecciona automáticamente el primer resultado: devuelve todos
        los candidatos encontrados para que el motor de matching decida.
        """
        # El formato es "APELLIDOS NOMBRES"
        apellidos_nombres = f"{apellido_paterno} {apellido_materno} {nombres}".strip()

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=self._headless)
                try:
                    page = await browser.new_page()
                    page.set_default_timeout(self._timeout_ms)

                    # 1. Abrir la página de consulta
                    await page.goto(
                        sri_selectors.URL_CONSULTA,
                        wait_until="domcontentloaded",
                    )

                    # 2. Hacer clic en "Continuar Navegando" si aparece
                    try:
                        await page.click(
                            "button:has-text('Continuar')",
                            timeout=5000,
                        )
                        await page.wait_for_timeout(2000)
                    except Exception:  # noqa: BLE001
                        logger.debug("sri_sin_boton_continuar")

                    # 3. Llenar el campo con "APELLIDOS NOMBRES"
                    await page.fill(
                        self._selectores.input_apellidos_nombres,
                        apellidos_nombres,
                    )

                    # 4. Hacer clic en "Consultar"
                    await page.click(self._selectores.boton_consultar)

                    # 5. Esperar a que carguen los resultados
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(3000)

                    # 6. Extraer los candidatos de la tabla de resultados
                    candidatos = await self._extraer_candidatos(page)

                    logger.info(
                        "sri_consulta_exitosa",
                        candidatos=len(candidatos),
                    )
                    return candidatos

                finally:
                    await browser.close()
        except FuenteCedulaNoDisponibleError:
            raise
        except Exception as exc:
            error_seguro = sanitizar_error_externo(exc)
            logger.error("sri_error", error=error_seguro)
            raise FuenteCedulaNoDisponibleError(
                f"SOURCE_UNAVAILABLE: error al consultar SRI: {error_seguro}"
            ) from exc

    async def _extraer_candidatos(self, page: Page) -> list[CedulaCandidateDTO]:
        """Extrae los candidatos de la tabla de resultados.

        Estructura confirmada (captura real 2026-10-04):
        `RUC / cédula | Razón social / Apellidos y nombres | ...`
        Ej: `1900748284 | ABAD CHINININ GLENDI LETICIA | ...`
        """
        import re

        candidatos: list[CedulaCandidateDTO] = []

        # Verificar si hay resultados
        tabla = await page.query_selector(self._selectores.tabla_resultados)
        if tabla is None:
            logger.info("sri_sin_resultados")
            return candidatos

        # Extraer filas de la tabla
        filas = await page.query_selector_all(self._selectores.filas_resultados)
        for fila in filas:
            celdas = await fila.query_selector_all("td, th")
            textos = [((await c.text_content()) or "").strip() for c in celdas]
            textos = [t for t in textos if t]
            if not textos:
                continue

            # Buscar la cédula (10 dígitos) en la primera celda
            cedula = None
            nombre_texto = None
            for i, texto in enumerate(textos):
                if re.match(r"^\d{10}$", texto):
                    cedula = texto
                    if i + 1 < len(textos):
                        nombre_texto = textos[i + 1]
                    break

            if cedula is None or nombre_texto is None:
                continue

            # El nombre viene en formato "APELLIDOS NOMBRES"
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
            logger.info("sri_sin_candidatos")
        return candidatos
