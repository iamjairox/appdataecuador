"""Schemas Pydantic: perfil academico, timeline e historial de un
funcionario -- Modulo 10, `GET /funcionarios/{persona_master_id}/{academico,timeline,historial}`."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PerfilAcademicoResponseSchema(BaseModel):
    """Forma EXACTA de `PerfilAcademicoDTO` (Submodulo 7.16) -- serializada
    tal cual la devuelve `PerfilAcademicoService`, sin recalcular nada."""

    model_config = ConfigDict(from_attributes=True)

    persona_master: dict[str, Any]
    identidad: dict[str, Any]
    titulos: list[dict[str, Any]] = Field(default_factory=list)
    historial: list[dict[str, Any]] = Field(default_factory=list)
    alertas: list[dict[str, Any]] = Field(default_factory=list)
    eventos: list[dict[str, Any]] = Field(default_factory=list)
    estadisticas: dict[str, Any] = Field(default_factory=dict)
    generado_en: datetime


class PuntoTimelineSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    origen: str
    descripcion: str
    referencia_id: int | None = None


class TimelineResponseSchema(BaseModel):
    """Forma de `TimelinePersonaDTO` (Submodulo 6.5) -- `TimelinePersonaService`,
    reutilizado tal cual."""

    model_config = ConfigDict(from_attributes=True)

    persona_master_id: int
    puntos: list[PuntoTimelineSchema] = Field(default_factory=list)


class VersionHistorialSchema(BaseModel):
    """UNA version del historial laboral de la persona -- `VersionFuncionario`
    (Modulo 5, `HistorialService.historial_de_persona`, REUTILIZADO)."""

    model_config = ConfigDict(from_attributes=True)

    entidad_id: int
    numero_version: int
    cargo: str
    dependencia: str
    area: str
    fecha_inicio: date
    fecha_fin: date | None = None
    correo: str | None = None
    telefono: str | None = None
