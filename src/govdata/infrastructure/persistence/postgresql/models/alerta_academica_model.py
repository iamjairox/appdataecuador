"""Modelo ORM: alerta_academica (Submodulo 7.8)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.estado_alerta_academica import EstadoAlertaAcademica
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_academica import TipoAlertaAcademica
from govdata.infrastructure.persistence.postgresql.models.base import Base


class AlertaAcademicaModel(Base):
    __tablename__ = "alerta_academica"
    __table_args__ = (
        Index("ix_alerta_academica_persona_master", "persona_master_id"),
        Index("ix_alerta_academica_estado", "estado"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[TipoAlertaAcademica] = mapped_column(
        Enum(TipoAlertaAcademica, name="tipo_alerta_academica_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    prioridad: Mapped[NivelCriticidad] = mapped_column(
        Enum(NivelCriticidad, name="nivel_criticidad_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    detectado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[EstadoAlertaAcademica] = mapped_column(
        Enum(EstadoAlertaAcademica, name="estado_alerta_academica_enum", values_callable=lambda e: [x.value for x in e]), nullable=False,
        default=EstadoAlertaAcademica.PENDIENTE,
    )
    titulo_academico_id: Mapped[int | None] = mapped_column(
        ForeignKey("titulo_academico.id", ondelete="SET NULL"), nullable=True
    )
