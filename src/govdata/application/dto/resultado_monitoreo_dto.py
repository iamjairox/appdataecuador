"""DTO: ResultadoMonitoreoDTO -- resultado de UNA corrida del Motor de
Monitoreo Continuo (Submodulo 5.15) sobre una entidad.

`comparacion` es `None` cuando el flujo termino temprano (sin documento
nuevo, o hash sin cambios -- nunca se llego a descargar/extraer/comparar);
`verificacion` SIEMPRE esta presente, incluso en ese caso (Submodulo
5.10/5.15: "mantener un historial de verificaciones incluso cuando no
haya cambios")."""

from __future__ import annotations

from dataclasses import dataclass

from govdata.application.dto.resultado_comparacion_dto import ResultadoComparacionDTO
from govdata.application.dto.verificacion_dto import VerificacionDTO


@dataclass(frozen=True, slots=True)
class ResultadoMonitoreoDTO:
    entidad_id: int
    hubo_cambio: bool
    verificacion: VerificacionDTO
    comparacion: ResultadoComparacionDTO | None = None
