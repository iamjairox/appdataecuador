"""Puerto: VerificacionRemotaPort -- Submodulo 5.15 (Motor de Monitoreo
Continuo): "Nunca descargar un documento si el hash no cambio".

Un SHA256 real de contenido remoto NUNCA puede conocerse sin descargar el
archivo completo -- eso es matematicamente imposible. Lo que SI permite
evitar una descarga innecesaria son las cabeceras HTTP condicionales
(`ETag`/`Last-Modified`), obtenidas con una peticion `HEAD` (liviana,
sin cuerpo) contra la misma URL. Este puerto es deliberadamente NUEVO y
SEPARADO de `HttpFetcherPort` (Modulo 3) -- no le agrega ni le cambia
ningun metodo, para no tocar el comportamiento ya aprobado del Modulo 3.

Contrato "fail-safe hacia adelante": si no se puede determinar con
certeza que el recurso NO cambio (servidor no soporta condicionales, HEAD
falla, no hay valores previos que comparar), la respuesta debe ser
`True` ("puede haber cambiado, hay que descargar") -- nunca se omite una
descarga real por un error de este chequeo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class VerificacionRemotaPort(ABC):
    """Verificacion ligera (sin descargar) de si un recurso remoto cambio."""

    @abstractmethod
    def hay_cambios(self, url: str, etag_conocido: str | None, last_modified_conocido: str | None) -> bool:
        """True si el recurso parece haber cambiado (o no se pudo
        determinar con certeza). False SOLO si el servidor confirma
        explicitamente que el recurso es identico al ya conocido."""
