"""Schemas Pydantic: Entidad -- Modulo 10."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class EntidadResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    tipo: str | None = Field(default=None, description="Tipo de institucion, si el descubrimiento lo capturo")
    provincia: str | None = Field(default=None, description="Aun no capturado por Transparencia (Modulo 2)")
    ciudad: str | None = Field(default=None, description="Aun no capturado por Transparencia (Modulo 2)")
    portal_origen: str
    estado: str = Field(description="'activa' | 'inactiva'")
    ultima_publicacion: date | None = None
    ultima_actualizacion: datetime | None = None
