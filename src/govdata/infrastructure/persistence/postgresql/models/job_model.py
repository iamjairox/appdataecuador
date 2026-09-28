"""Modelo ORM: jobs."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.entities.job import JobStatus, TipoJob
from govdata.infrastructure.persistence.postgresql.models.base import Base


class JobModel(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tipo: Mapped[TipoJob] = mapped_column(Enum(TipoJob, name="tipo_job_enum", values_callable=lambda e: [x.value for x in e]), nullable=False)
    entidad_id: Mapped[int | None] = mapped_column(
        ForeignKey("entidades.id", ondelete="SET NULL"), nullable=True
    )
    estado: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum", values_callable=lambda e: [x.value for x in e]), nullable=False, index=True
    )
    porcentaje: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    errores: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    reintentos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
