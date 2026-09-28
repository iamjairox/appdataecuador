"""Schema Pydantic: Cambio de Entidad -- Modulo 10, `GET /entidades/{id}/cambios`."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class CambioResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    persona_id: int
    numero_version: int
    cargo: str
    dependencia: str
    fecha_inicio: date
    fecha_fin: date | None = None
    tipo_cambio: str | None = None
    criticidad: str | None = None
