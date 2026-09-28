"""Modelo ORM: titulo_version (Submodulos 7.6/7.14, historial append-only)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.entities.titulo_version_academica import EstadoVersionAcademica
from govdata.domain.value_objects.estado_registro_academico import EstadoRegistroAcademico
from govdata.infrastructure.persistence.postgresql.models.base import Base


class TituloVersionAcademicaModel(Base):
    __tablename__ = "titulo_version"
    __table_args__ = (
        Index("ix_titulo_version_persona_master", "persona_master_id", "clave_titulo"),
        Index("ix_titulo_version_vigente", "persona_master_id", "clave_titulo", "estado_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    clave_titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False)
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
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado_version: Mapped[EstadoVersionAcademica] = mapped_column(
        Enum(EstadoVersionAcademica, name="estado_version_academica_enum", values_callable=lambda e: [x.value for x in e]), nullable=False,
        default=EstadoVersionAcademica.VIGENTE,
    )
    consulta_senescyt_id: Mapped[int] = mapped_column(
        ForeignKey("consulta_senescyt.id", ondelete="CASCADE"), nullable=False
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
