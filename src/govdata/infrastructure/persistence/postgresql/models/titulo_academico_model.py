"""Modelo ORM: titulo_academico (Submodulo 7.6, puntero vigente)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.estado_registro_academico import EstadoRegistroAcademico
from govdata.infrastructure.persistence.postgresql.models.base import Base


class TituloAcademicoModel(Base):
    __tablename__ = "titulo_academico"
    __table_args__ = (
        Index("ix_titulo_academico_persona_master", "persona_master_id"),
        Index("ix_titulo_academico_clave", "persona_master_id", "clave_titulo", "vigente"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    clave_titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    nivel: Mapped[str] = mapped_column(String(100), nullable=False)
    institucion: Mapped[str] = mapped_column(String(300), nullable=False)
    fecha_registro: Mapped[date | None] = mapped_column(Date, nullable=True)
    pais: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estado: Mapped[EstadoRegistroAcademico] = mapped_column(
        Enum(EstadoRegistroAcademico, name="estado_registro_academico_enum", values_callable=lambda e: [x.value for x in e]),
        nullable=False, default=EstadoRegistroAcademico.DESCONOCIDO,
    )
    modalidad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    numero_registro: Mapped[str | None] = mapped_column(String(100), nullable=True)
    area_conocimiento: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tipo_titulo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fecha_graduacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fuente: Mapped[str] = mapped_column(String(50), nullable=False, default="senescyt")
    fecha_consulta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    nivel_confianza: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    version_fuente: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    evidencia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
