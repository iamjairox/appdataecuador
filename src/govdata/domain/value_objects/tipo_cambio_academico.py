"""Value Object: TipoCambioAcademico -- Submodulo 7.7 (Comparador
Academico). Mismo patron que `TipoCambio` (Modulo 5): `CAMBIO_MULTIPLE`
se agrega por consistencia arquitectonica (dos o mas campos cambiados a
la vez en el mismo titulo) aunque la especificacion no lo liste
explicitamente -- decision de diseno documentada, no una omision."""

from __future__ import annotations

from enum import Enum


class TipoCambioAcademico(str, Enum):
    TITULO_NUEVO = "titulo_nuevo"
    TITULO_ELIMINADO = "titulo_eliminado"
    CAMBIO_UNIVERSIDAD = "cambio_universidad"
    CAMBIO_NIVEL = "cambio_nivel"
    CAMBIO_MODALIDAD = "cambio_modalidad"
    CAMBIO_REGISTRO = "cambio_registro"
    CAMBIO_ESTADO = "cambio_estado"
    CAMBIO_FECHA = "cambio_fecha"
    CAMBIO_MULTIPLE = "cambio_multiple"
    SIN_CAMBIOS = "sin_cambios"
