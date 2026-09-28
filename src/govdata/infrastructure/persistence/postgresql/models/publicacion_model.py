"""Modelo ORM: publicaciones."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class PublicacionModel(Base):
    __tablename__ = "publicaciones"
    __table_args__ = (UniqueConstraint("entidad_id", "mes_publicado", name="uq_publicacion_entidad_mes"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entidad_id: Mapped[int] = mapped_column(ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False)
    mes_publicado: Mapped[date] = mapped_column(Date, nullable=False)
    url_item: Mapped[str] = mapped_column(String(1000), nullable=False)
    detectado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
