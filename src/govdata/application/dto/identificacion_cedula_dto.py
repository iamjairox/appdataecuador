"""Contratos puros para la identificacion por nombre en fuentes externas."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EstadoMatchingCedula(str, Enum):
    MATCH_EXACT = "match_exact"
    MATCH_HIGH_CONFIDENCE = "match_high_confidence"
    AMBIGUOUS = "ambiguous"
    NO_MATCH = "no_match"
    SOURCE_UNAVAILABLE = "source_unavailable"
    NO_CEDULA_FOUND = "no_cedula_found"


@dataclass(frozen=True, slots=True)
class CedulaCandidateDTO:
    cedula: str
    nombres: str
    apellido_paterno: str = ""
    apellido_materno: str = ""
    datos_adicionales: dict[str, Any] = field(default_factory=dict)

    @property
    def nombre_completo(self) -> str:
        return " ".join(
            parte for parte in (self.nombres, self.apellido_paterno, self.apellido_materno) if parte
        )


@dataclass(frozen=True, slots=True)
class ResultadoMatchingCedulaDTO:
    estado: EstadoMatchingCedula
    candidato: CedulaCandidateDTO | None = None
    confianza: float = 0.0
    candidatos: tuple[CedulaCandidateDTO, ...] = ()
    detalle: str | None = None
