"""Modelo ORM: consultas_fuente_log (Submodulo 6.10, Historial de
Consultas)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.infrastructure.persistence.postgresql.models.base import Base


class ConsultaFuenteLogModel(Base):
    __tablename__ = "consultas_fuente_log"
    __table_args__ = (
        Index("ix_consulta_fuente_persona_master", "persona_master_id", "fuente", "iniciado_en"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    fuente: Mapped[FuenteExterna] = mapped_column(Enum(FuenteExterna, name="fuente_externa_enum", values_callable=lambda e: [x.value for x in e]), nullable=False)
    iniciado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exito: Mapped[bool | None] = mapped_column(nullable=True)
    duracion_segundos: Mapped[float | None] = mapped_column(Float, nullable=True)
    reintentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
