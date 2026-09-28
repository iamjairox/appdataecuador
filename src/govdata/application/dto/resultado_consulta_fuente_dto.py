"""DTO: ResultadoConsultaFuenteDTO -- lo que retorna un `ExternalSourcePort`
(Submodulo 6.6) al consultar una fuente externa por unas senales de
identidad."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from govdata.domain.value_objects.fuente_externa import FuenteExterna


@dataclass(frozen=True, slots=True)
class ResultadoConsultaFuenteDTO:
    fuente: FuenteExterna
    encontrado: bool
    consultado_en: datetime
    datos: dict[str, Any] = field(default_factory=dict)
