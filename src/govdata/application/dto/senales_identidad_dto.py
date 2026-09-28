"""DTO: SenalesIdentidadDTO -- las senales comparables de UN registro
(existente o nuevo) que el Motor de Resolucion de Identidad (Submodulo
6.2) usa para decidir si dos registros son la misma Persona.

Deliberadamente plano (solo texto/None): tanto una `PersonaMaster` ya
persistida como la respuesta cruda de una fuente externa (que todavia no
tiene una PersonaMaster asignada) se traducen a este mismo DTO antes de
compararse -- el motor de scoring nunca conoce el origen del dato.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SenalesIdentidadDTO:
    nombre: str
    apellido: str
    correo: str | None = None
    telefono: str | None = None
    institucion: str | None = None
    cargo: str | None = None
    fingerprint: str | None = None
    fingerprint_fonetico: str | None = None
