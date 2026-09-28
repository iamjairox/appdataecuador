"""Modelo ORM: auditoria_etapa (Submodulos 9.10/9.15)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.estado_paso import EstadoPaso
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline
from govdata.infrastructure.persistence.postgresql.models.base import Base


class AuditoriaEtapaModel(Base):
    __tablename__ = "auditoria_etapa"
    __table_args__ = (
        Index("ix_auditoria_etapa_trabajo", "trabajo_orquestador_id"),
        Index("ix_auditoria_etapa_tipo_paso", "tipo_paso"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trabajo_orquestador_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trabajo_orquestador.id", ondelete="CASCADE"), nullable=False
    )
    tipo_paso: Mapped[TipoPasoPipeline] = mapped_column(
        Enum(TipoPasoPipeline, name="tipo_paso_pipeline_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    estado_paso: Mapped[EstadoPaso] = mapped_column(Enum(EstadoPaso, name="estado_paso_enum", values_callable=lambda e: [x.value for x in e]), nullable=False)
    iniciado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    razon_omision: Mapped[str | None] = mapped_column(Text, nullable=True)
    cantidad_registros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    cache_utilizada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version_utilizada: Mapped[str | None] = mapped_column(String(100), nullable=True)
