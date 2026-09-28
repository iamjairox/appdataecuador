"""Modelo ORM: oportunidades_comerciales (Submodulo 5.17, preparacion para un futuro CRM)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.entities.oportunidad_comercial import TipoOportunidad
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.infrastructure.persistence.postgresql.models.base import Base


class OportunidadComercialModel(Base):
    __tablename__ = "oportunidades_comerciales"
    __table_args__ = (Index("ix_oportunidad_entidad", "entidad_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    entidad_id: Mapped[int] = mapped_column(ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False)
    persona_id: Mapped[int | None] = mapped_column(ForeignKey("personas.id", ondelete="SET NULL"), nullable=True)
    tipo: Mapped[TipoOportunidad] = mapped_column(Enum(TipoOportunidad, name="tipo_oportunidad_enum", values_callable=lambda e: [x.value for x in e]), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    detectado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    prioridad: Mapped[NivelCriticidad] = mapped_column(
        Enum(NivelCriticidad, name="nivel_criticidad_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
