"""Directorio local de compañías publicado por Supercias."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class CompaniaModel(Base):
    __tablename__ = "companias_supercias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ruc: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    expediente: Mapped[str | None] = mapped_column(String(40), nullable=True)
    nombre: Mapped[str] = mapped_column(String(600), index=True)
    situacion_legal: Mapped[str | None] = mapped_column(String(250), nullable=True)
    provincia: Mapped[str | None] = mapped_column(String(120), nullable=True)
    canton: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ciudad: Mapped[str | None] = mapped_column(String(120), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(80), nullable=True)
    representante: Mapped[str | None] = mapped_column(String(350), nullable=True)
    cargo_representante: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ciiu_nivel_1: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ciiu_nivel_6: Mapped[str | None] = mapped_column(String(50), nullable=True)
    es_juridica: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    periodo_fuente: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cargado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RepresentanteCompaniaModel(Base):
    __tablename__ = "representantes_companias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    compania_id: Mapped[int] = mapped_column(ForeignKey("companias_supercias.id", ondelete="CASCADE"), unique=True)
    nombre: Mapped[str] = mapped_column(String(350))
    actividad_economica: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    cedula: Mapped[str | None] = mapped_column(String(20), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(320), nullable=True)
    celular: Mapped[str | None] = mapped_column(String(50), nullable=True)
    telefono_domicilio: Mapped[str | None] = mapped_column(String(80), nullable=True)
    telefono_oficina: Mapped[str | None] = mapped_column(String(80), nullable=True)
    direccion_domicilio: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    direccion_oficina: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    estado: Mapped[str] = mapped_column(String(80), default="pendiente")
    consultado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
