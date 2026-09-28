"""Modelo ORM: atributos_trazables (Submodulo 6.15, Trazabilidad)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.infrastructure.persistence.postgresql.models.base import Base


class AtributoTrazableModel(Base):
    __tablename__ = "atributos_trazables"
    __table_args__ = (Index("ix_atributo_trazable_persona_master", "persona_master_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    campo: Mapped[str] = mapped_column(String(100), nullable=False)
    valor: Mapped[str] = mapped_column(Text, nullable=False)
    fuente: Mapped[FuenteExterna] = mapped_column(Enum(FuenteExterna, name="fuente_externa_enum", values_callable=lambda e: [x.value for x in e]), nullable=False)
    obtenido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    registro_fuente_id: Mapped[int | None] = mapped_column(
        ForeignKey("registros_fuente.id", ondelete="SET NULL"), nullable=True
    )
