"""DTO: PersonaAcademicaDTO -- Submodulo 7.3, EL UNICO DTO academico.

"Todo el sistema utilizara unicamente este DTO." El adaptador SENESCYT
(Submodulo 7.2) transforma CUALQUIER forma de respuesta cruda a este
DTO antes de que llegue a cualquier otra capa; el normalizador (7.4), el
comparador (7.7), el motor de alertas (7.8) y el de eventos (7.9) solo
conocen esta forma -- nunca el JSON crudo de SENESCYT.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class PersonaAcademicaDTO:
    titulo: str
    nivel: str
    institucion: str
    fecha_registro: date | None = None
    pais: str | None = None
    estado: str | None = None
    modalidad: str | None = None
    numero_registro: str | None = None
    area_conocimiento: str | None = None
    tipo_titulo: str | None = None
    fecha_graduacion: date | None = None
    observaciones: str | None = None
