"""Modelo ORM: entidades."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class EntidadModel(Base):
    __tablename__ = "entidades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(500), nullable=False)
    url_transparencia: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    portal_origen: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_extra: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
