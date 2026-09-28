"""DTOs: PuntoTimelineDTO y TimelineEntidadDTO -- Submodulo 5.13.

Cada punto de la linea de tiempo de una entidad corresponde a UNA
verificacion (hubo o no hubo cambio -- ver Submodulo 5.15, "mantener un
historial de verificaciones incluso cuando no haya cambios") con su
documento, version, cantidad de cambios detectados y cantidad de alertas
generadas en esa verificacion."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from govdata.application.dto.resultado_unificado_dto import EntidadResumenDTO


@dataclass(frozen=True, slots=True)
class PuntoTimelineDTO:
    verificado_en: datetime
    documento_id: int | None
    version_documento: int | None
    hubo_cambio: bool
    cantidad_cambios: int
    cantidad_alertas: int
    mes_publicado: date | None = None
    """Mes que cubre el documento verificado (si se pudo resolver)."""


@dataclass(frozen=True, slots=True)
class TimelineEntidadDTO:
    entidad: EntidadResumenDTO
    puntos: list[PuntoTimelineDTO] = field(default_factory=list)
