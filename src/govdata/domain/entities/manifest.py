"""Entidad de dominio: Manifest.

Registro CANONICO y append-only de cada version de archivo efectivamente
almacenada. Mientras `Descarga` audita el INTENTO (incluyendo fallos),
`Manifest` solo existe para descargas EXITOSAS -- es el "de donde saco
exactamente este archivo" que cualquier modulo futuro (extraccion,
clasificacion) puede consultar sin tener que re-derivar nada:

    {
      "documento_id": 15234,
      "url": "...",
      "sha256": "...",
      "mime": "application/pdf",
      "bytes": 234567,
      "fecha_descarga": "...",
      "storage_uri": "minio://documentos-transparencia/ab/ab34.../archivo.pdf"
    }

Si el mismo `Documento` se redescarga y el archivo cambio (hash distinto),
se crea un Manifest NUEVO (no se sobreescribe el anterior) -- eso es lo
que permite reconstruir el historial completo de versiones de un
documento, no solo la ultima.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import GovDataError


class ManifestInvalidoError(GovDataError):
    """Un registro de Manifest no cumple sus invariantes."""


@dataclass(slots=True)
class Manifest:
    """Registro canonico de una version de archivo almacenada."""

    documento_id: int
    url: str
    sha256: str
    mime: str
    bytes_totales: int
    storage_uri: str
    fecha_descarga: datetime
    id: int | None = None

    def __post_init__(self) -> None:
        if len(self.sha256) != 64:
            raise ManifestInvalidoError(f"sha256 invalido: '{self.sha256}'")
        if self.bytes_totales < 0:
            raise ManifestInvalidoError(f"bytes_totales invalido: {self.bytes_totales}")
        if not self.storage_uri or not self.storage_uri.strip():
            raise ManifestInvalidoError("Manifest requiere storage_uri")
        if not self.mime or not self.mime.strip():
            raise ManifestInvalidoError("Manifest requiere mime")
