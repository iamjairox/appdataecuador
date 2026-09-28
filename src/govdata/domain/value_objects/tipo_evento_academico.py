"""Value Object: TipoEventoAcademico -- Submodulo 7.9 (Motor de Eventos)."""

from __future__ import annotations

from enum import Enum


class TipoEventoAcademico(str, Enum):
    TITULO_NUEVO = "titulo_nuevo"
    TITULO_ELIMINADO = "titulo_eliminado"
    CAMBIO_NIVEL = "cambio_nivel"
    CAMBIO_UNIVERSIDAD = "cambio_universidad"
    CAMBIO_ESTADO = "cambio_estado"
    CONSULTA_EXITOSA = "consulta_exitosa"
    CONSULTA_FALLIDA = "consulta_fallida"
