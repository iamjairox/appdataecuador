"""Modelo ORM: evento_foro (Submodulo 8.7)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.estado_evento_foro import EstadoEventoForo
from govdata.domain.value_objects.tipo_evento_foro import TipoEventoForo
from govdata.infrastructure.persistence.postgresql.models.base import Base


class EventoForoModel(Base):
    __tablename__ = "evento_foro"
    __table_args__ = (
        Index("ix_evento_foro_estado", "estado"),
        Index("ix_evento_foro_persona_master", "persona_master_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tipo: Mapped[TipoEventoForo] = mapped_column(Enum(TipoEventoForo, name="tipo_evento_foro_enum", values_callable=lambda e: [x.value for x in e]), nullable=False)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    estado: Mapped[EstadoEventoForo] = mapped_column(
        Enum(EstadoEventoForo, name="estado_evento_foro_enum", values_callable=lambda e: [x.value for x in e]), nullable=False, default=EstadoEventoForo.PENDIENTE,
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    procesado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
