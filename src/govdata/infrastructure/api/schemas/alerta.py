"""Schemas Pydantic: Alerta -- Modulo 10."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertaResponseSchema(BaseModel):
    """`GET /entidades/{id}/alertas` -- `Alerta` (Modulo 5, congelado)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    entidad_id: int
    tipo: str
    prioridad: str
    descripcion: str
    detectado_en: datetime
    estado: str
    persona_id: int | None = None
    documento_id: int | None = None


class AlertaFuncionarioResponseSchema(BaseModel):
    """`GET /funcionarios/{persona_master_id}/alertas` -- agregado de
    Modulos 6/7/8 (`AlertaFuncionarioDTO`, Modulo 10)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    fuente: str
    tipo: str
    prioridad: str
    descripcion: str
    detectado_en: datetime
    estado: str
