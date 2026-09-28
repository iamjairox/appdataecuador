"""Value Object: TipoEventoForo -- Submodulo 8.7 (Motor de Eventos)."""

from __future__ import annotations

from enum import Enum


class TipoEventoForo(str, Enum):
    REGISTRO_NUEVO = "registro_nuevo"
    REGISTRO_ELIMINADO = "registro_eliminado"
    CAMBIO_ESTADO = "cambio_estado"
    CAMBIO_PROVINCIA = "cambio_provincia"
    CAMBIO_REGISTRO = "cambio_registro"
    CAMBIO_DATO = "cambio_dato"
    CONSULTA_EXITOSA = "consulta_exitosa"
    CONSULTA_FALLIDA = "consulta_fallida"
