"""Adaptador: DpeScraperAdapter.

Implementacion de `PortalScraperPort` para el portal de Transparencia de
la Defensoria del Pueblo (`transparencia.dpe.gob.ec`).

Decision de diseno (documentada explicitamente): el portal es una SPA de
React donde las filas de la tabla de entidades NO tienen `href` (navegan
via JS router), lo que en principio obligaria a hacer click-por-fila para
descubrir cada entidad -- carisimo para ~1900 entidades. Se verifico que
la propia SPA consume una serie de endpoints JSON publicos, no
autenticados, para renderizarse (`RUTA_LISTADO_ENTIDADES`, etc, ver
`selectors/dpe_selectors.py`). Este adaptador usa el
`BrowserContext.request` de Playwright (que comparte cookies/headers del
contexto real del navegador) para leer esos mismos JSON directamente, en
lugar de driver clicks + parsing de texto renderizado:

    - Sigue siendo 100% Playwright (mismo browser context, mismo pool).
    - Es MAS resiliente ante cambios visuales/CSS que el texto scraping
      original (un rediseno de la UI no rompe el JSON subyacente).
    - Nunca descarga el contenido de un archivo -- solo lee metadata JSON
      sobre que archivos existen y donde estan.

Un fallback DOM (click-based) queda documentado como extension futura si
en produccion se detecta que el contrato JSON dejo de ser confiable (ver
`PortalScraperPort` para el punto de extension: bastaria una nueva clase
que implemente el mismo puerto).

Todos los errores de Playwright/red se traducen a excepciones de dominio
(`domain.exceptions`) para que la politica de reintentos compartida
(`shared.retry.retry_policy`) pueda clasificarlos sin conocer Playwright.
"""

from __future__ import annotations

from typing import Any

from playwright.sync_api import APIResponse, BrowserContext
from playwright.sync_api import Error as PlaywrightError

from govdata.application.dto.descubrimiento_dto import ArchivoDTO, NumeralPublicadoDTO
from govdata.application.dto.entidad_dto import EntidadDescubiertaDTO
from govdata.application.ports.portal_scraper_port import PortalScraperPort
from govdata.config.logging_config import get_logger
from govdata.domain.exceptions.domain_exceptions import (
    DescargaFallidaError,
    EntidadNoEncontradaError,
    ExtraccionFallidaError,
)
from govdata.infrastructure.scraping.playwright.selectors import dpe_selectors
from govdata.infrastructure.scraping.rate_limiter import RateLimiter
from govdata.shared.retry.retry_policy import con_reintentos

logger = get_logger(__name__)

_HTTP_NO_ENCONTRADO = 404
_HTTP_LIMITE_TASA = 429


class DpeScraperAdapter(PortalScraperPort):
    """Adaptador Playwright para `transparencia.dpe.gob.ec`."""

    def __init__(
        self,
        contexto: BrowserContext,
        rate_limiter: RateLimiter,
        url_origen: str,
        max_reintentos: int = 3,
        backoff_base_segundos: float = 2.0,
    ) -> None:
        self._contexto = contexto
        self._rate_limiter = rate_limiter
        self._url_origen = url_origen.rstrip("/")
        # Solo la parte de RED se reintenta (backoff exponencial); errores
        # de parseo (ExtraccionFallidaError) son permanentes -- reintentar
        # una respuesta malformada no la va a arreglar.
        self._get_con_reintentos = con_reintentos(
            max_intentos=max_reintentos, espera_inicial_segundos=backoff_base_segundos
        )(self._get_respuesta)

    def listar_entidades(self) -> list[EntidadDescubiertaDTO]:
        cuerpo = self._obtener_json(dpe_selectors.RUTA_LISTADO_ENTIDADES, contexto="listado de entidades")
        if not isinstance(cuerpo, dict) or "results" not in cuerpo:
            raise ExtraccionFallidaError(
                "Respuesta inesperada del listado de entidades: falta la clave 'results'"
            )

        entidades: list[EntidadDescubiertaDTO] = []
        for grupo in cuerpo.get("results", []):
            for item in grupo.get("data", []):
                entidad_id = item.get("id")
                nombre = item.get("name")
                if entidad_id is None or not nombre:
                    logger.warning("entidad_descartada_datos_incompletos", item=item)
                    continue
                entidades.append(
                    EntidadDescubiertaDTO(
                        nombre=str(nombre).strip(),
                        url_transparencia=f"{self._url_origen}/entidades/{entidad_id}",
                        portal_origen="dpe",
                        identificador_portal=str(entidad_id),
                        tipo_institucion=item.get("function_organization"),
                        activo=bool(item.get("is_active", True)),
                    )
                )
        return entidades

    def listar_meses_publicados(self, url_entidad: str, anio: int) -> list[int]:
        establishment_id = self._extraer_id_entidad(url_entidad)
        ruta = (
            f"{dpe_selectors.RUTA_MESES_PUBLICADOS}"
            f"?establishment_id={establishment_id}&year={anio}&type={dpe_selectors.TIPO_TRANSPARENCIA_ACTIVA}"
        )
        cuerpo = self._obtener_json(ruta, contexto=f"meses publicados anio={anio}")
        if not isinstance(cuerpo, list):
            raise ExtraccionFallidaError(
                f"Respuesta inesperada de meses publicados (anio={anio}): se esperaba una lista"
            )
        return [item["month"] for item in cuerpo if isinstance(item, dict) and "month" in item]

    def listar_publicaciones_mes(
        self, url_entidad: str, anio: int, mes: int
    ) -> list[NumeralPublicadoDTO]:
        establishment_id = self._extraer_id_entidad(url_entidad)
        ruta = (
            f"{dpe_selectors.RUTA_PUBLICACIONES_MES}"
            f"?month={mes}&year={anio}&establishment_id={establishment_id}"
        )
        cuerpo = self._obtener_json(ruta, contexto=f"publicaciones {anio}-{mes:02d}")
        if not isinstance(cuerpo, list):
            raise ExtraccionFallidaError(
                f"Respuesta inesperada de publicaciones ({anio}-{mes:02d}): se esperaba una lista"
            )

        numerales: list[NumeralPublicadoDTO] = []
        for item in cuerpo:
            numeral_raw = item.get("numeral") or {}
            archivos = [
                ArchivoDTO(
                    descripcion=str(archivo.get("description", "")),
                    nombre=str(archivo.get("name", "")),
                    url_descarga=self._url_absoluta(str(archivo.get("url_download", ""))),
                )
                for archivo in item.get("files", [])
            ]
            numerales.append(
                NumeralPublicadoDTO(
                    descripcion=str(numeral_raw.get("description", "")),
                    archivos=archivos,
                )
            )
        return numerales

    # -- helpers internos -------------------------------------------------

    def _obtener_json(self, ruta: str, contexto: str) -> Any:
        url = f"{self._url_origen}{ruta}"
        respuesta = self._get_con_reintentos(url, contexto)

        try:
            return respuesta.json()
        except Exception as exc:
            raise ExtraccionFallidaError(f"Respuesta no-JSON para {contexto} ({url})") from exc

    def _get_respuesta(self, url: str, contexto: str) -> APIResponse:
        """Parte transitoria (red) de una peticion -- unica envuelta en reintentos."""
        self._rate_limiter.esperar_turno()
        try:
            respuesta = self._contexto.request.get(url)
        except PlaywrightError as exc:
            raise DescargaFallidaError(f"Error de red al consultar {contexto} ({url}): {exc}") from exc
        except TimeoutError as exc:
            raise DescargaFallidaError(f"Timeout al consultar {contexto} ({url})") from exc

        if respuesta.status == _HTTP_NO_ENCONTRADO:
            raise EntidadNoEncontradaError(f"Recurso no encontrado ({contexto}): {url}")
        if respuesta.status == _HTTP_LIMITE_TASA or respuesta.status >= 500:
            raise DescargaFallidaError(f"Portal respondio {respuesta.status} para {contexto} ({url})")
        if not respuesta.ok:
            raise DescargaFallidaError(f"Portal respondio {respuesta.status} para {contexto} ({url})")
        return respuesta

    @staticmethod
    def _extraer_id_entidad(url_entidad: str) -> str:
        """Extrae el identificador numerico de `.../entidades/{id}`."""
        partes = url_entidad.rstrip("/").rsplit("/", 1)
        if len(partes) != 2 or not partes[1]:
            raise ExtraccionFallidaError(f"No se pudo extraer el id de entidad desde: {url_entidad}")
        return partes[1]

    def _url_absoluta(self, ruta: str) -> str:
        if ruta.startswith(("http://", "https://")):
            return ruta
        return f"{self._url_origen}{ruta}"
