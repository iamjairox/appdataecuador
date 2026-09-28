"""DTOs: Timeline de Persona -- Submodulo 6.5.

Une, en orden cronologico, el historial institucional ya existente
(Modulo 5, `HistorialService.historial_de_persona`, REUTILIZADO -- nunca
reimplementado) con las versiones de fuentes externas (Modulo 6,
`RegistroFuente`) para dar una unica linea de tiempo por Persona:

    2019 Municipio Quito -> 2021 Ministerio Salud -> 2023 Procuraduria
    -> 2026 Director Juridico

"Nunca perder historial": cada punto conserva su origen (institucional o
fuente externa) y el identificador del registro que lo respalda.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True, slots=True)
class PuntoTimelinePersonaDTO:
    fecha_inicio: date | None
    fecha_fin: date | None
    origen: str
    """`"institucional"` (viene de `VersionFuncionario`, Modulo 5) o el
    valor de una `FuenteExterna` (`"senescyt"`, `"foro_abogados"`, ...)."""
    descripcion: str
    referencia_id: int | None = None


@dataclass(frozen=True, slots=True)
class TimelinePersonaDTO:
    persona_master_id: int
    puntos: list[PuntoTimelinePersonaDTO] = field(default_factory=list)
