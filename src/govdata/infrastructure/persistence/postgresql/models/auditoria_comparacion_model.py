"""Modelo ORM: auditorias_comparacion (Submodulo 5.9)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class AuditoriaComparacionModel(Base):
    __tablename__ = "auditorias_comparacion"
    __table_args__ = (Index("ix_auditoria_documento", "documento_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entidad_id: Mapped[int] = mapped_column(ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False)
    documento_id: Mapped[int] = mapped_column(ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False)
    version_documento: Mapped[int] = mapped_column(Integer, nullable=False)
    ejecutado_por: Mapped[str] = mapped_column(String(200), nullable=False)
    iniciado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duracion_segundos: Mapped[float | None] = mapped_column(Float, nullable=True)
    cambios_detectados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errores: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
