"""Modelo ORM: alertas_perfil (Submodulo 6.13)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.estado_alerta_perfil import EstadoAlertaPerfil
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_perfil import TipoAlertaPerfil
from govdata.infrastructure.persistence.postgresql.models.base import Base


class AlertaPerfilModel(Base):
    __tablename__ = "alertas_perfil"
    __table_args__ = (Index("ix_alerta_perfil_persona_master", "persona_master_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[TipoAlertaPerfil] = mapped_column(
        Enum(TipoAlertaPerfil, name="tipo_alerta_perfil_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    prioridad: Mapped[NivelCriticidad] = mapped_column(
        Enum(NivelCriticidad, name="nivel_criticidad_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    detectado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[EstadoAlertaPerfil] = mapped_column(
        Enum(EstadoAlertaPerfil, name="estado_alerta_perfil_enum", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoAlertaPerfil.PENDIENTE,
    )
    registro_fuente_id: Mapped[int | None] = mapped_column(
        ForeignKey("registros_fuente.id", ondelete="SET NULL"), nullable=True
    )
