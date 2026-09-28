"""Value Object: TipoCambioForo -- Submodulo 8.5 (Comparador Foro).

Las 4 categorias explicitas del Submodulo 8.7 ("Cambio de estado. Cambio
de provincia. Cambio de registro. Cambio de cualquier dato del Foro.")
mas la simetria NUEVO/ELIMINADO (mismo patron que `TipoCambioAcademico`,
Modulo 7). A diferencia de Modulo 7 -- que necesito un `CAMBIO_MULTIPLE`
explicito porque su ultima categoria de alerta era "cambio de institucion"
(un campo concreto) -- aqui la propia especificacion (8.7) ya nombra un
catch-all generico ("cambio de CUALQUIER dato"): `CAMBIO_DATO` cubre tanto
un unico campo sin categoria dedicada (`nombre_completo`, `cedula`) COMO
2+ campos modificados a la vez -- decision documentada, no una omision."""

from __future__ import annotations

from enum import Enum


class TipoCambioForo(str, Enum):
    DATO_NUEVO = "dato_nuevo"
    DATO_ELIMINADO = "dato_eliminado"
    CAMBIO_ESTADO = "cambio_estado"
    CAMBIO_PROVINCIA = "cambio_provincia"
    CAMBIO_REGISTRO = "cambio_registro"
    CAMBIO_DATO = "cambio_dato"
    SIN_CAMBIOS = "sin_cambios"
