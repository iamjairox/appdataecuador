"""Modelo ORM: eventos (Submodulo 5.7, cola de notificaciones -- preparacion)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.entities.evento import EstadoEvento, TipoEvento
from govdata.infrastructure.persistence.postgresql.models.base import Base


class EventoModel(Base):
    __tablename__ = "eventos"
    __table_args__ = (Index("ix_evento_estado", "estado"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tipo: Mapped[TipoEvento] = mapped_column(Enum(TipoEvento, name="tipo_evento_enum", values_callable=lambda e: [x.value for x in e]), nullable=False)
    entidad_id: Mapped[int] = mapped_column(ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False)
    referencia_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    estado: Mapped[EstadoEvento] = mapped_column(
        Enum(EstadoEvento, name="estado_evento_enum", values_callable=lambda e: [x.value for x in e]), nullable=False, default=EstadoEvento.PENDIENTE
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    procesado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
