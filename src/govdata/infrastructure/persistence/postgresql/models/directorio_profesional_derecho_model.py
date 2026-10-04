"""Listado local, público y ligero de profesionales del Derecho."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class DirectorioProfesionalDerechoModel(Base):
    __tablename__ = "directorio_profesionales_derecho"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo_foro: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    matricula: Mapped[str | None] = mapped_column(String(80), nullable=True)
    nombre_completo: Mapped[str] = mapped_column(String(350), index=True, nullable=False)
    direccion_oficina: Mapped[str | None] = mapped_column(String(700), nullable=True)
    inscripcion: Mapped[str | None] = mapped_column(String(150), nullable=True)
    credencial: Mapped[str | None] = mapped_column(String(80), nullable=True)
    estado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cargado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EstadoDirectorioProfesionalesModel(Base):
    __tablename__ = "estado_directorio_profesionales_derecho"

    id: Mapped[int] = mapped_column(primary_key=True)
    total_esperado: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pagina_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    registros_guardados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="inactivo")
    mensaje: Mapped[str | None] = mapped_column(String(500), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
