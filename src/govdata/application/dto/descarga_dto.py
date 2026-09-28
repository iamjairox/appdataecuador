"""DTO: RespuestaDescargaDTO.

Salida cruda de `HttpFetcherPort.descargar()`, antes de cualquier
validacion de negocio (esa vive en `domain.rules.validador_contenido_archivo`
y en `DescargarDocumentoUseCase`).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RespuestaDescargaDTO:
    """Respuesta HTTP cruda de una descarga."""

    codigo_http: int
    contenido: bytes
    content_type: str | None
    etag: str | None
    last_modified: str | None
