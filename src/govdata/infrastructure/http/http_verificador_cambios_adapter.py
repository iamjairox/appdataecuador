"""Adaptador: HttpVerificadorCambiosAdapter -- implementa `VerificacionRemotaPort`.

Peticion `HEAD` (sin cuerpo, liviana) para leer `ETag`/`Last-Modified` sin
descargar el archivo. Completamente independiente de `RequestsHttpFetcherAdapter`
(Modulo 3): usa su PROPIA `requests.Session`, no reintentos compartidos, y
NUNCA se invoca desde el flujo de descarga real -- solo desde el Motor de
Monitoreo Continuo (Modulo 5, Submodulo 5.15), antes de decidir si vale
la pena descargar.

Fail-safe estricto: cualquier problema (timeout, 4xx/5xx, servidor sin
soporte de condicionales, sin valores previos que comparar) responde
`True` ("hay que descargar") -- nunca se omite una descarga real por un
fallo de este chequeo.
"""

from __future__ import annotations

import requests

from govdata.application.ports.verificacion_remota_port import VerificacionRemotaPort
from govdata.config.logging_config import get_logger

logger = get_logger(__name__)


class HttpVerificadorCambiosAdapter(VerificacionRemotaPort):
    def __init__(self, timeout_segundos: float = 10.0, user_agent: str = "GovDataIntelligencePlatform/1.0") -> None:
        self._timeout_segundos = timeout_segundos
        self._sesion = requests.Session()
        self._sesion.headers.update({"User-Agent": user_agent})

    def hay_cambios(self, url: str, etag_conocido: str | None, last_modified_conocido: str | None) -> bool:
        if not etag_conocido and not last_modified_conocido:
            # Nada contra que comparar -- no se puede afirmar "sin cambios".
            return True

        try:
            respuesta = self._sesion.head(url, timeout=self._timeout_segundos, allow_redirects=True)
        except requests.RequestException as exc:
            logger.warning("verificacion_remota_fallo", url=url, error=str(exc))
            return True

        if respuesta.status_code >= 400:
            logger.warning("verificacion_remota_status_error", url=url, status=respuesta.status_code)
            return True

        etag_remoto = respuesta.headers.get("ETag")
        last_modified_remoto = respuesta.headers.get("Last-Modified")

        if etag_conocido and etag_remoto:
            return etag_remoto != etag_conocido
        if last_modified_conocido and last_modified_remoto:
            return last_modified_remoto != last_modified_conocido

        # El servidor no devolvio ningun condicional comparable.
        return True

    def cerrar(self) -> None:
        self._sesion.close()
