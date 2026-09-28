"""Modelo ORM: historial_foro (Submodulo 8.6, bitacora de cambios)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo
from govdata.infrastructure.persistence.postgresql.models.base import Base


class HistorialForoModel(Base):
    __tablename__ = "historial_foro"
    __table_args__ = (Index("ix_historial_foro_persona_master", "persona_master_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    clave_registro: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo_cambio: Mapped[TipoCambioForo] = mapped_column(
        Enum(TipoCambioForo, name="tipo_cambio_foro_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    detectado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consulta_foro_id: Mapped[int] = mapped_column(ForeignKey("consulta_foro.id", ondelete="CASCADE"), nullable=False)
    ejecutado_por: Mapped[str] = mapped_column(String(100), nullable=False, default="sistema")
    registro_foro_id: Mapped[int | None] = mapped_column(
        ForeignKey("registro_foro.id", ondelete="SET NULL"), nullable=True
    )
    campos_modificados: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
