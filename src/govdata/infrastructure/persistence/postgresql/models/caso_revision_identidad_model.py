"""Modelo ORM: casos_revision_identidad (Submodulo 6.21, Motor de
Confianza y Revision Manual)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.estado_revision_identidad import EstadoRevisionIdentidad
from govdata.infrastructure.persistence.postgresql.models.base import Base


class CasoRevisionIdentidadModel(Base):
    __tablename__ = "casos_revision_identidad"
    __table_args__ = (Index("ix_caso_revision_estado", "estado"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    persona_master_id_a: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    persona_master_id_b: Mapped[int | None] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=True
    )
    registro_fuente_id: Mapped[int | None] = mapped_column(
        ForeignKey("registros_fuente.id", ondelete="SET NULL"), nullable=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    explicacion: Mapped[str] = mapped_column(Text, nullable=False)
    campos_utilizados: Mapped[list] = mapped_column(JSON, nullable=False)
    estado: Mapped[EstadoRevisionIdentidad] = mapped_column(
        Enum(EstadoRevisionIdentidad, name="estado_revision_identidad_enum", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoRevisionIdentidad.PENDIENTE_REVISION,
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resuelto_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resuelto_por: Mapped[str | None] = mapped_column(String(200), nullable=True)
    criterio_resolucion: Mapped[str | None] = mapped_column(String(200), nullable=True)
