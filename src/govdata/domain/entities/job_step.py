"""Entidad de dominio: JobStep -- historial append-only de las
transiciones de estado de un `Job` (Submodulo 4.8)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.job import JobStatus
from govdata.domain.exceptions.domain_exceptions import GovDataError


class JobStepInvalidoError(GovDataError):
    """Un JobStep no cumple sus invariantes."""


@dataclass(slots=True)
class JobStep:
    """Un paso individual (una transicion de estado) dentro de un Job."""

    job_id: uuid.UUID
    estado: JobStatus
    iniciado_en: datetime
    id: int | None = None
    finalizado_en: datetime | None = None
    mensaje: str | None = None

    def __post_init__(self) -> None:
        if self.finalizado_en is not None and self.finalizado_en < self.iniciado_en:
            raise JobStepInvalidoError("finalizado_en no puede ser anterior a iniciado_en")

    @property
    def duracion_segundos(self) -> float | None:
        if self.finalizado_en is None:
            return None
        return (self.finalizado_en - self.iniciado_en).total_seconds()
