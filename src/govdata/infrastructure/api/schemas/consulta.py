"""Schema Pydantic: Consulta de Entidad -- Modulo 10.

Forma EXACTA de `ResultadoOrquestacionDTO` (Submodulo 9.14, EL CONTRATO
OFICIAL de `GovDataPipelineOrchestrator`) -- la API nunca reconstruye
esta forma, solo la serializa tal cual la devuelve el Orquestador."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConsultaEntidadResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job: dict[str, Any]
    entidad: dict[str, Any] = Field(default_factory=dict)
    estadisticas: dict[str, Any] = Field(default_factory=dict)
    funcionarios: list[dict[str, Any]] = Field(default_factory=list)
    alertas: list[dict[str, Any]] = Field(default_factory=list)
    errores: list[str] = Field(default_factory=list)
    duracion_total: str
    generado_en: datetime
