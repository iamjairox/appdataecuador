"""Regla de dominio: ruta de almacenamiento content-addressable.

Usar el hash SHA-256 del contenido (en vez del nombre original del
archivo) como parte de la ruta logra deduplicacion automatica a nivel de
storage: si el mismo contenido se descarga dos veces (misma entidad
redescargada, o dos entidades que por error publican el mismo archivo),
ambas terminan escribiendo a la MISMA clave -- la segunda escritura es
un no-op idempotente. El "sharding" en subcarpetas de 2 caracteres evita
miles de archivos en un solo directorio plano.
"""

from __future__ import annotations

from govdata.domain.entities.documento import TipoArchivo


def construir_ruta_almacenamiento(sha256: str, tipo_archivo: TipoArchivo) -> str:
    """`{ab}/{sha256}.{ext}` -- determinista: mismo contenido, misma ruta."""
    prefijo = sha256[:2]
    return f"{prefijo}/{sha256}.{tipo_archivo.value}"
