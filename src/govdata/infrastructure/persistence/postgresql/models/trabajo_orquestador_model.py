"""Modelo ORM: trabajo_orquestador (Submodulos 9.6/9.7/9.8, cola persistente)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from govdata.infrastructure.persistence.postgresql.models.base import Base


class TrabajoOrquestadorModel(Base):
    __tablename__ = "trabajo_orquestador"
    __table_args__ = (
        Index("ix_trabajo_orquestador_estado", "estado"),
        Index("ix_trabajo_orquestador_estado_prioridad", "estado", "prioridad"),
        Index("ix_trabajo_orquestador_entidad", "entidad_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tipo: Mapped[TipoTrabajoOrquestador] = mapped_column(
        Enum(TipoTrabajoOrquestador, name="tipo_trabajo_orquestador_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    parametros: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    politica: Mapped[str] = mapped_column(String(100), nullable=False, default="consulta_rapida")
    estado: Mapped[EstadoTrabajoOrquestador] = mapped_column(
        Enum(EstadoTrabajoOrquestador, name="estado_trabajo_orquestador_enum", values_callable=lambda e: [x.value for x in e]), nullable=False,
        default=EstadoTrabajoOrquestador.PENDIENTE,
    )
    prioridad: Mapped[NivelPrioridadEjecucion] = mapped_column(
        Enum(NivelPrioridadEjecucion, name="nivel_prioridad_ejecucion_enum", values_callable=lambda e: [x.value for x in e]), nullable=False,
        default=NivelPrioridadEjecucion.MEDIA,
    )
    version_lock: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    entidad_id: Mapped[int | None] = mapped_column(ForeignKey("entidades.id", ondelete="SET NULL"), nullable=True)
    creado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actualizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    iniciado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ultimo_error: Mapped[str | None] = mapped_column(Text, nullable=True)
