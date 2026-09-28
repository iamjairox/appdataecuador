"""DTO: PerfilPersonaDTO -- Submodulo 6.16, EL CONTRATO OFICIAL del
Motor de Identidad.

Forma EXACTA pedida por el cliente:

    {
      "persona": {},
      "identidad": {},
      "perfil": {},
      "fuentes": [],
      "historial": [],
      "eventos": [],
      "alertas": [],
      "timeline": [],
      "estadisticas": {}
    }

Sera el contrato oficial para los modulos futuros (SENESCYT, Dashboard,
API, n8n) -- nunca romper este contrato, igual que `ResultadoComparacionDTO`
(Modulo 5) y `ResultadoUnificadoDTO` (Modulo 4).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class PerfilPersonaDTO:
    """`{"persona": {}, "identidad": {}, "perfil": {}, "fuentes": [],
    "historial": [], "eventos": [], "alertas": [], "timeline": [],
    "estadisticas": {}}`."""

    persona: dict[str, Any]
    identidad: dict[str, Any]
    perfil: dict[str, Any]
    fuentes: list[dict[str, Any]] = field(default_factory=list)
    historial: list[dict[str, Any]] = field(default_factory=list)
    eventos: list[dict[str, Any]] = field(default_factory=list)
    alertas: list[dict[str, Any]] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    estadisticas: dict[str, Any] = field(default_factory=dict)
    generado_en: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        """Serializacion exacta del contrato (para logging/API/n8n futuros)."""
        return asdict(self)
