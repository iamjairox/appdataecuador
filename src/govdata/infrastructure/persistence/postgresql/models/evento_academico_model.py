"""Modelo ORM: evento_academico (Submodulo 7.9)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.estado_evento_academico import EstadoEventoAcademico
from govdata.domain.value_objects.tipo_evento_academico import TipoEventoAcademico
from govdata.infrastructure.persistence.postgresql.models.base import Base


class EventoAcademicoModel(Base):
    __tablename__ = "evento_academico"
    __table_args__ = (
        Index("ix_evento_academico_estado", "estado"),
        Index("ix_evento_academico_persona_master", "persona_master_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tipo: Mapped[TipoEventoAcademico] = mapped_column(
        Enum(TipoEventoAcademico, name="tipo_evento_academico_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    estado: Mapped[EstadoEventoAcademico] = mapped_column(
        Enum(EstadoEventoAcademico, name="estado_evento_academico_enum", values_callable=lambda e: [x.value for x in e]), nullable=False,
        default=EstadoEventoAcademico.PENDIENTE,
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    procesado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
