"""Adaptador Playwright para el Foro de Abogados de la Función Judicial.

Implementa `ForoAbogadosPort` usando Playwright para interactuar con la
página real del Foro de Abogados, como lo haría una persona manualmente:

    1. Abrir la página del Foro de Abogados
    2. Llenar el campo CEDULA
    3. Hacer clic en el botón "Aceptar"
    4. Esperar a que cargue la respuesta
    5. Extraer la información profesional disponible

Los selectores están centralizados en `foro_abogados_selectors.py`.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from playwright.async_api import Page, async_playwright

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.ports.foro_abogados_port import ForoAbogadosPort
from govdata.config.settings import get_settings
from govdata.config.logging_config import get_logger
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import GovDataError
from govdata.domain.rules.matching_cedula import hacer_matching_cedula
from govdata.application.dto.identificacion_cedula_dto import EstadoMatchingCedula
from govdata.application.services.consulta_cedula_cascada import consultar_cedula_en_cascada
from govdata.infrastructure.scraping.playwright.bloqueo_antibot import pagina_bloqueada_por_antibot
from govdata.infrastructure.scraping.playwright.fuentes_cedula import fuentes_consulta_cedula
from govdata.infrastructure.scraping.playwright.selectors import foro_abogados_selectors
from govdata.shared.security.redaccion_datos_personales import sanitizar_error_externo

logger = get_logger(__name__)


def _ejecutar_async_desde_sync(corutina: Any) -> Any:
    """Ejecuta una corutina sin anidar loops dentro del orquestador."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(corutina)
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, corutina).result()


class FuenteForoNoDisponibleError(GovDataError):
    """La fuente no esta disponible para la consulta."""


@dataclass(frozen=True, slots=True)
class SelectoresForoAbogados:
    """Selectores centralizados para el Foro de Abogados."""

    input_cedula: str = foro_abogados_selectors.SELECTOR_INPUT_CEDULA
    boton_aceptar: str = foro_abogados_selectors.SELECTOR_BOTON_ACEPTAR
    tabla_resultados: str = foro_abogados_selectors.SELECTOR_TABLA_RESULTADOS
    campo_email: str = "#EMAIL"
    campo_celular: str = "#CELULAR"
    campo_nombres: str = "#NOMBRES"
    campo_apellidos: str = "#APELLIDOS"
    campo_telefono_domicilio: str = "#TELEFONODO"
    campo_direccion_domicilio: str = "#DIRECCIONDO"
    campo_telefono_oficina: str = "#TELEFONOOF"
    campo_direccion_oficina: str = "#DIRECCIONOF"
    filas_resultados: str = "table tbody tr"


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

    async def buscar_por_cedula(self, cedula: str) -> list[RegistroForoDTO]:
        """Busca un abogado por cédula en el Foro de Abogados.

        La cédula es únicamente una llave técnica transitoria: se usa para
        consultar el registro profesional, pero nunca se almacena en logs,
        respuestas de API, ni exportaciones.
        """
        return await self._buscar_por_cedula_async(cedula)

    async def _buscar_por_cedula_async(self, cedula: str) -> list[RegistroForoDTO]:
        """Implementación asíncrona de la búsqueda por cédula."""
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=self._headless)
                try:
                    page = await browser.new_page()
                    page.set_default_timeout(self._timeout_ms)

                    # El sitio muestra un `alert()` después de validar una
                    # cédula registrada. Aceptarlo equivale al segundo clic
                    # que se hace manualmente y permite que la página termine
                    # de cargar los campos del perfil.
                    def aceptar_aviso(dialog: Any) -> None:
                        asyncio.create_task(dialog.accept())

                    page.on("dialog", aceptar_aviso)

                    # 1. Abrir la página del Foro de Abogados
                    await page.goto(
                        foro_abogados_selectors.URL_CONSULTA,
                        wait_until="domcontentloaded",
                    )

                    # Verificar si hay CAPTCHA o challenge
                    contenido = await page.content()
                    if get_settings().scraping.rechazar_captcha_antibot and self._detectar_captcha(contenido):
                        logger.warning("foro_captcha_detectado")
                        raise FuenteForoNoDisponibleError(
                            "SOURCE_UNAVAILABLE: CAPTCHA detectado en el Foro de Abogados"
                        )

                    # 2. Llenar el campo CEDULA
                    await page.fill(self._selectores.input_cedula, cedula)

                    # 3. Hacer clic en el botón "Aceptar"
                    await page.click(self._selectores.boton_aceptar)

                    # 4. Esperar a que cargue la respuesta
                    await page.wait_for_load_state("networkidle")

                    # Verificar si hay CAPTCHA después del envío
                    contenido = await page.content()
                    if get_settings().scraping.rechazar_captcha_antibot and self._detectar_captcha(contenido):
                        logger.warning("foro_captcha_detectado")
                        raise FuenteForoNoDisponibleError(
                            "SOURCE_UNAVAILABLE: CAPTCHA detectado en el Foro de Abogados"
                        )

                    # 5. Extraer la información profesional disponible
                    registros = await self._extraer_registros(page, cedula)

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

    async def _extraer_registros(self, page: Page, cedula: str) -> list[RegistroForoDTO]:
        """Extrae los registros del Foro de Abogados desde la página.
        
        Usa el parser HTML existente (foro_html_parser) para extraer todos los
        campos disponibles de manera robusta, incluyendo celular y correo.
        
        La cédula se guarda en el registro para que aparezca en todas las consultas.
        """
        from govdata.config.rule_engine_foro import cargar_rule_engine_foro
        from govdata.infrastructure.http.foro_html_parser import parsear_registro_foro

        registros: list[RegistroForoDTO] = []

        # Obtener el HTML de la página
        html = await page.content()

        # Cargar el catálogo de campos desde el motor de reglas
        rule_engine = cargar_rule_engine_foro()
        catalogo = rule_engine.campos

        # El HTML conserva la estructura, pero el Foro llena varios `input`
        # con JavaScript; `page.content()` no siempre serializa sus valores.
        # Por eso se combinan ambos orígenes, priorizando el valor vivo.
        registro = parsear_registro_foro(html, catalogo)
        valores = await self._extraer_valores_vivos(page)
        if registro or any(valores.values()):
            registros.append(
                RegistroForoDTO(
                    nombre_completo=valores["nombre_completo"] or (registro.nombre_completo if registro else None),
                    registro=registro.registro if registro else None,
                    provincia=registro.provincia if registro else None,
                    estado=registro.estado if registro else None,
                    cedula=cedula,
                    celular=valores["celular"] or (registro.celular if registro else None),
                    correo=valores["correo"] or (registro.correo if registro else None),
                    telefono_domicilio=valores["telefono_domicilio"],
                    direccion_domicilio=valores["direccion_domicilio"],
                    telefono_oficina=valores["telefono_oficina"],
                    direccion_oficina=valores["direccion_oficina"],
                )
            )

        return registros

    async def _extraer_valores_vivos(self, page: Page) -> dict[str, str | None]:
        async def leer(selector: str) -> str | None:
            campo = page.locator(selector)
            if await campo.count() == 0:
                return None
            valor = (await campo.input_value()).strip()
            return valor or None

        # La respuesta del Foro rellena estos valores mediante JavaScript
        # después de terminar la navegación. Se espera de forma acotada para
        # no confundir una respuesta todavía en carga con "sin datos".
        for _ in range(12):
            nombres = await leer(self._selectores.campo_nombres)
            apellidos = await leer(self._selectores.campo_apellidos)
            correo = await leer(self._selectores.campo_email)
            celular = await leer(self._selectores.campo_celular)
            telefono_domicilio = await leer(self._selectores.campo_telefono_domicilio)
            direccion_domicilio = await leer(self._selectores.campo_direccion_domicilio)
            telefono_oficina = await leer(self._selectores.campo_telefono_oficina)
            direccion_oficina = await leer(self._selectores.campo_direccion_oficina)
            if any((correo, celular, telefono_domicilio, direccion_domicilio, telefono_oficina, direccion_oficina)):
                return {
                    "nombre_completo": " ".join(parte for parte in (nombres, apellidos) if parte) or None,
                    "correo": correo,
                    "celular": celular,
                    "telefono_domicilio": telefono_domicilio,
                    "direccion_domicilio": direccion_domicilio,
                    "telefono_oficina": telefono_oficina,
                    "direccion_oficina": direccion_oficina,
                }
            await page.wait_for_timeout(250)

        return {
            "nombre_completo": None,
            "correo": None,
            "celular": None,
            "telefono_domicilio": None,
            "direccion_domicilio": None,
            "telefono_oficina": None,
            "direccion_oficina": None,
        }

    def _detectar_captcha(self, contenido: str) -> bool:
        return pagina_bloqueada_por_antibot(contenido)

    @staticmethod
    def _requiere_confirmacion_registro(contenido: str) -> bool:
        """Reconoce el aviso previo al perfil de un registro existente."""
        texto = " ".join(contenido.lower().split())
        return (
            "ya se encuentra registrada" in texto
            or "ya se encuentra registrado" in texto
            or "ya consta registrado" in texto
        )

    def buscar_por_persona(self, persona: Persona) -> list[RegistroForoDTO]:
        """Resuelve una cédula transitoria cuando Transparencia no la trae.

        Se usa únicamente en el pipeline síncrono de entidad. La cédula no
        se escribe en `Persona`, logs ni respuestas; solo encadena la
        identificación exacta con la consulta oficial del Foro.
        """
        return _ejecutar_async_desde_sync(self._buscar_por_persona_async(persona))

    async def _buscar_por_persona_async(self, persona: Persona) -> list[RegistroForoDTO]:
        if persona.cedula:
            return await self.buscar_por_cedula(persona.cedula)

        nombre = persona.nombre_completo
        partes = nombre.apellidos.split()
        paterno, materno = (partes + [""])[:2]
        candidatos = await consultar_cedula_en_cascada(
            fuentes_consulta_cedula(), nombre.nombres, paterno, materno
        )
        coincidencia = hacer_matching_cedula(nombre.nombres, nombre.apellidos, candidatos)
        if coincidencia.candidato is None or coincidencia.estado not in {
            EstadoMatchingCedula.MATCH_EXACT,
            EstadoMatchingCedula.MATCH_HIGH_CONFIDENCE,
        }:
            return []
        return await self.buscar_por_cedula(coincidencia.candidato.cedula)

    def buscar_por_persona_master(self, persona_master: Any) -> list[RegistroForoDTO]:
        raise FuenteForoNoDisponibleError(
            "SOURCE_UNAVAILABLE: el Foro de Abogados solo permite búsqueda por cédula"
        )
