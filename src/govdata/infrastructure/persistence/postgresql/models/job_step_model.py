"""Modelo ORM: job_steps."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.entities.job import JobStatus
from govdata.infrastructure.persistence.postgresql.models.base import Base


class JobStepModel(Base):
    __tablename__ = "job_steps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    estado: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status_enum", values_callable=lambda e: [x.value for x in e]), nullable=False)
    iniciado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mensaje: Mapped[str | None] = mapped_column(Text, nullable=True)
