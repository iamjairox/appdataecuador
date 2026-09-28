"""Modelo ORM: eventos_perfil (Submodulo 6.12)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.estado_evento_perfil import EstadoEventoPerfil
from govdata.domain.value_objects.tipo_evento_identidad import TipoEventoIdentidad
from govdata.infrastructure.persistence.postgresql.models.base import Base


class EventoPerfilModel(Base):
    __tablename__ = "eventos_perfil"
    __table_args__ = (Index("ix_evento_perfil_estado", "estado"), Index("ix_evento_perfil_persona_master", "persona_master_id"))

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tipo: Mapped[TipoEventoIdentidad] = mapped_column(
        Enum(TipoEventoIdentidad, name="tipo_evento_identidad_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    estado: Mapped[EstadoEventoPerfil] = mapped_column(
        Enum(EstadoEventoPerfil, name="estado_evento_perfil_enum", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoEventoPerfil.PENDIENTE,
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    procesado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
