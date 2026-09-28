"""DTO: ResultadoOrquestacionDTO -- Submodulo 9.14, EL CONTRATO OFICIAL
del `GovDataPipelineOrchestrator`.

Forma EXACTA pedida por el cliente:

    {
      "job": {},
      "entidad": {},
      "estadisticas": {},
      "funcionarios": [],
      "alertas": [],
      "errores": [],
      "duracion_total": ""
    }

Nunca romper este contrato -- mismo criterio que `ResultadoConsultaEntidadDTO`
(Modulo 8, Submodulo 8.11) y `PerfilConsolidadoDTO` (Modulo 8, Submodulo
8.10). Es el ultimo eslabon de la cadena de contratos oficiales de todo
el sistema: el usuario "solo pedira informacion de una entidad" y esto es
exactamente lo que recibe de vuelta."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ResultadoOrquestacionDTO:
    """`{"job": {}, "entidad": {}, "estadisticas": {}, "funcionarios": [],
    "alertas": [], "errores": [], "duracion_total": ""}`."""

    job: dict[str, Any]
    entidad: dict[str, Any] = field(default_factory=dict)
    estadisticas: dict[str, Any] = field(default_factory=dict)
    funcionarios: list[dict[str, Any]] = field(default_factory=list)
    alertas: list[dict[str, Any]] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    duracion_total: str = "0.0s"
    generado_en: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        """Serializacion exacta del contrato (para logging/API/n8n futuros)."""
        return asdict(self)
