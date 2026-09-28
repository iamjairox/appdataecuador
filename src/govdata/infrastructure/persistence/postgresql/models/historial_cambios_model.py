"""Modelo ORM: historial_cambios."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class HistorialCambiosModel(Base):
    __tablename__ = "historial_cambios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id", ondelete="CASCADE"), nullable=False)
    entidad_id: Mapped[int] = mapped_column(ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False)
    funcionario_id: Mapped[int | None] = mapped_column(
        ForeignKey("funcionarios.id", ondelete="SET NULL"), nullable=True
    )
    campo_modificado: Mapped[str] = mapped_column(String(100), nullable=False)
    valor_anterior: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_nuevo: Mapped[str | None] = mapped_column(Text, nullable=True)
    detectado_en: Mapped[date] = mapped_column(Date, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
