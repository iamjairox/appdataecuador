"""Modelo ORM: ejecuciones (auditoria de corridas del pipeline)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class EjecucionModel(Base):
    __tablename__ = "ejecuciones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entidad_id: Mapped[int | None] = mapped_column(
        ForeignKey("entidades.id", ondelete="SET NULL"), nullable=True
    )
    etapa: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)  # exito|fallo|reintento
    mensaje_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    intentos: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    iniciado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
