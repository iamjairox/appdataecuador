"""Value Object: TipoAlertaForo -- Submodulo 8.7 (Motor de Alertas):
"Alertar cuando: Cambio de estado. Cambio de provincia. Cambio de
registro. Cambio de cualquier dato del Foro." Se agregan
REGISTRO_NUEVO/REGISTRO_ELIMINADO por simetria con `TipoAlertaAcademica`
(Modulo 7) -- una matricula nueva o eliminada es, con mas razon, digna de
alerta que un cambio de dato menor."""

from __future__ import annotations

from enum import Enum


class TipoAlertaForo(str, Enum):
    REGISTRO_NUEVO = "registro_nuevo"
    REGISTRO_ELIMINADO = "registro_eliminado"
    CAMBIO_ESTADO = "cambio_estado"
    CAMBIO_PROVINCIA = "cambio_provincia"
    CAMBIO_REGISTRO = "cambio_registro"
    CAMBIO_DATO = "cambio_dato"
