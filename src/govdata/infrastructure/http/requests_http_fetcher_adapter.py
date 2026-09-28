"""Adaptador: RequestsHttpFetcherAdapter.

Implementacion de `HttpFetcherPort` con `requests`, en streaming (no carga
todo a memoria de una sola vez desde la red -- se lee por chunks, lo que
permite cortar temprano si el archivo excede `tamano_maximo_bytes`, sin
descargarlo completo primero).

Mantiene una `requests.Session` propia (reutiliza conexiones TCP/pool
entre descargas sucesivas -- mejora real de rendimiento bajo la cola).
`requests.Session` NO es segura para compartir entre hilos: cada hilo del
`DescargaOrchestratorService` (Modulo 3) debe crear SU PROPIA instancia de
este adaptador, nunca compartir una.

Solo la parte de RED se reintenta (backoff exponencial compartido, ver
`shared.retry.retry_policy`); errores de validacion de tamano son
permanentes y se propagan de inmediato.
"""

from __future__ import annotations

import requests
from requests import Response

from govdata.application.dto.descarga_dto import RespuestaDescargaDTO
from govdata.application.ports.http_fetcher_port import HttpFetcherPort
from govdata.domain.exceptions.domain_exceptions import (
    ContenidoInvalidoError,
    DescargaFallidaError,
    RecursoNoDisponibleError,
)
from govdata.shared.retry.retry_policy import con_reintentos

_HTTP_NO_ENCONTRADO = (404, 410)
_HTTP_LIMITE_TASA = 429
_TAMANO_CHUNK = 65_536


class RequestsHttpFetcherAdapter(HttpFetcherPort):
    """Descarga HTTP simple, en streaming, con reintentos."""

    def __init__(
        self,
        timeout_segundos: float = 30.0,
        max_reintentos: int = 3,
        backoff_base_segundos: float = 2.0,
        tamano_maximo_bytes: int | None = None,
        user_agent: str = "GovDataIntelligencePlatform/1.0",
    ) -> None:
        self._timeout_segundos = timeout_segundos
        self._tamano_maximo_bytes = tamano_maximo_bytes
        self._user_agent = user_agent
        self._sesion = requests.Session()
        self._descargar_con_reintentos = con_reintentos(
            max_intentos=max_reintentos, espera_inicial_segundos=backoff_base_segundos
        )(self._descargar_raw)

    def descargar(self, url: str) -> RespuestaDescargaDTO:
        return self._descargar_con_reintentos(url)

    def cerrar(self) -> None:
        self._sesion.close()

    def _descargar_raw(self, url: str) -> RespuestaDescargaDTO:
        try:
            respuesta = self._sesion.get(
                url,
                timeout=self._timeout_segundos,
                stream=True,
                headers={"User-Agent": self._user_agent},
            )
        except requests.Timeout as exc:
            raise DescargaFallidaError(f"Timeout descargando {url}") from exc
        except requests.RequestException as exc:
            raise DescargaFallidaError(f"Error de red descargando {url}: {exc}") from exc

        try:
            self._validar_status(respuesta, url)
            contenido = self._leer_contenido(respuesta, url)
        finally:
            respuesta.close()

        return RespuestaDescargaDTO(
            codigo_http=respuesta.status_code,
            contenido=contenido,
            content_type=respuesta.headers.get("Content-Type"),
            etag=respuesta.headers.get("ETag"),
            last_modified=respuesta.headers.get("Last-Modified"),
        )

    @staticmethod
    def _validar_status(respuesta: Response, url: str) -> None:
        if respuesta.status_code in _HTTP_NO_ENCONTRADO:
            raise RecursoNoDisponibleError(f"Recurso no encontrado ({respuesta.status_code}): {url}")
        if respuesta.status_code == _HTTP_LIMITE_TASA or respuesta.status_code >= 500:
            raise DescargaFallidaError(f"Servidor respondio {respuesta.status_code} para {url}")
        if not respuesta.ok:
            raise DescargaFallidaError(f"Servidor respondio {respuesta.status_code} para {url}")

    def _leer_contenido(self, respuesta: Response, url: str) -> bytes:
        contenido = bytearray()
        try:
            for chunk in respuesta.iter_content(chunk_size=_TAMANO_CHUNK):
                contenido.extend(chunk)
                if self._tamano_maximo_bytes is not None and len(contenido) > self._tamano_maximo_bytes:
                    raise ContenidoInvalidoError(
                        f"El archivo excede el tamano maximo permitido "
                        f"({self._tamano_maximo_bytes} bytes): {url}"
                    )
        except requests.RequestException as exc:
            raise DescargaFallidaError(f"Conexion interrumpida descargando {url}: {exc}") from exc
        return bytes(contenido)
