"""Modelo ORM: registro_foro (Submodulo 8.1, puntero vigente)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.estado_registro_foro import EstadoRegistroForo
from govdata.infrastructure.persistence.postgresql.models.base import Base


class RegistroForoModel(Base):
    __tablename__ = "registro_foro"
    __table_args__ = (
        Index("ix_registro_foro_persona_master", "persona_master_id"),
        Index("ix_registro_foro_clave", "persona_master_id", "clave_registro", "vigente"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    clave_registro: Mapped[str] = mapped_column(String(200), nullable=False)
    nombre_completo: Mapped[str | None] = mapped_column(String(300), nullable=True)
    registro: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provincia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estado: Mapped[EstadoRegistroForo] = mapped_column(
        Enum(EstadoRegistroForo, name="estado_registro_foro_enum", values_callable=lambda e: [x.value for x in e]), nullable=False, default=EstadoRegistroForo.DESCONOCIDO,
    )
    cedula: Mapped[str | None] = mapped_column(String(20), nullable=True)
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fuente: Mapped[str] = mapped_column(String(50), nullable=False, default="foro_abogados")
    fecha_consulta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    nivel_confianza: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    version_fuente: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    evidencia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
