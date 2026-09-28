"""Modelo ORM: verificaciones (Submodulos 5.10/5.15)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class VerificacionModel(Base):
    __tablename__ = "verificaciones"
    __table_args__ = (Index("ix_verificacion_entidad", "entidad_id", "verificado_en"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entidad_id: Mapped[int] = mapped_column(ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False)
    documento_id: Mapped[int | None] = mapped_column(
        ForeignKey("documentos.id", ondelete="SET NULL"), nullable=True
    )
    hubo_cambio: Mapped[bool] = mapped_column(Boolean, nullable=False)
    motivo: Mapped[str] = mapped_column(String(200), nullable=False)
    hash_verificado: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verificado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
