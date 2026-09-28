"""Modelo ORM: registro_foro_version (Submodulos 8.6/8.14, historial append-only)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.entities.registro_foro_version import EstadoVersionForo
from govdata.domain.value_objects.estado_registro_foro import EstadoRegistroForo
from govdata.infrastructure.persistence.postgresql.models.base import Base


class RegistroForoVersionModel(Base):
    __tablename__ = "registro_foro_version"
    __table_args__ = (
        Index("ix_registro_foro_version_persona_master", "persona_master_id", "clave_registro"),
        Index("ix_registro_foro_version_vigente", "persona_master_id", "clave_registro", "estado_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    clave_registro: Mapped[str] = mapped_column(String(200), nullable=False)
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre_completo: Mapped[str | None] = mapped_column(String(300), nullable=True)
    registro: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provincia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estado: Mapped[EstadoRegistroForo] = mapped_column(
        Enum(EstadoRegistroForo, name="estado_registro_foro_enum", values_callable=lambda e: [x.value for x in e]), nullable=False, default=EstadoRegistroForo.DESCONOCIDO,
    )
    cedula: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado_version: Mapped[EstadoVersionForo] = mapped_column(
        Enum(EstadoVersionForo, name="estado_version_foro_enum", values_callable=lambda e: [x.value for x in e]), nullable=False, default=EstadoVersionForo.VIGENTE,
    )
    consulta_foro_id: Mapped[int] = mapped_column(ForeignKey("consulta_foro.id", ondelete="CASCADE"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
