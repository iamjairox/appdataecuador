"""DTO: PerfilAcademicoDTO -- Submodulo 7.16, EL CONTRATO OFICIAL del
Motor de Enriquecimiento Academico.

Forma EXACTA pedida por el cliente:

    {
      "persona_master": {},
      "identidad": {},
      "titulos": [],
      "historial": [],
      "alertas": [],
      "eventos": [],
      "estadisticas": {},
      "generado_en": ""
    }

Nunca romper este contrato -- mismo criterio que `PerfilPersonaDTO`
(Modulo 6) y `ResultadoComparacionDTO` (Modulo 5).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class PerfilAcademicoDTO:
    """`{"persona_master": {}, "identidad": {}, "titulos": [], "historial":
    [], "alertas": [], "eventos": [], "estadisticas": {}, "generado_en": ""}`."""

    persona_master: dict[str, Any]
    identidad: dict[str, Any]
    titulos: list[dict[str, Any]] = field(default_factory=list)
    historial: list[dict[str, Any]] = field(default_factory=list)
    alertas: list[dict[str, Any]] = field(default_factory=list)
    eventos: list[dict[str, Any]] = field(default_factory=list)
    estadisticas: dict[str, Any] = field(default_factory=dict)
    generado_en: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        """Serializacion exacta del contrato (para logging/API/n8n futuros)."""
        return asdict(self)
