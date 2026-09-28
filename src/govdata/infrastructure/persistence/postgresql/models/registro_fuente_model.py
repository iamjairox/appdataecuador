"""Modelo ORM: registros_fuente (Submodulo 6.9, Versionado por Fuente)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.infrastructure.persistence.postgresql.models.base import Base


class RegistroFuenteModel(Base):
    __tablename__ = "registros_fuente"
    __table_args__ = (
        Index("ix_registro_fuente_persona_master", "persona_master_id"),
        Index("ix_registro_fuente_vigente", "persona_master_id", "fuente", "vigente"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    fuente: Mapped[FuenteExterna] = mapped_column(Enum(FuenteExterna, name="fuente_externa_enum", values_callable=lambda e: [x.value for x in e]), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    datos: Mapped[dict] = mapped_column(JSON, nullable=False)
    consultado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hash_contenido: Mapped[str | None] = mapped_column(String(64), nullable=True)
