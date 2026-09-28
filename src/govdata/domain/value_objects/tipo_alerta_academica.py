"""Value Object: TipoAlertaAcademica -- Submodulo 7.8 (Motor de Alertas)."""

from __future__ import annotations

from enum import Enum


class TipoAlertaAcademica(str, Enum):
    NUEVO_TITULO = "nuevo_titulo"
    TITULO_ELIMINADO = "titulo_eliminado"
    REGISTRO_SUSPENDIDO = "registro_suspendido"
    REGISTRO_ANULADO = "registro_anulado"
    CAMBIO_NIVEL = "cambio_nivel"
    CAMBIO_INSTITUCION = "cambio_institucion"
    CAMBIO_ESTADO = "cambio_estado"
