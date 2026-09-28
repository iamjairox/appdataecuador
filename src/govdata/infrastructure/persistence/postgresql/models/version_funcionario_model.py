"""Modelo ORM: versiones_funcionario (historial append-only, Submodulos 5.2-5.4)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.entities.version_funcionario import EstadoVersion
from govdata.infrastructure.persistence.postgresql.models.base import Base


class VersionFuncionarioModel(Base):
    __tablename__ = "versiones_funcionario"
    __table_args__ = (
        Index("ix_version_persona_entidad", "persona_id", "entidad_id"),
        Index("ix_version_entidad_cargo", "entidad_id", "cargo"),
        Index("ix_version_vigente", "persona_id", "entidad_id", "estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id", ondelete="CASCADE"), nullable=False)
    entidad_id: Mapped[int] = mapped_column(ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False)
    funcionario_id: Mapped[int | None] = mapped_column(
        ForeignKey("funcionarios.id", ondelete="SET NULL"), nullable=True
    )
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False)
    cargo: Mapped[str] = mapped_column(String(300), nullable=False)
    dependencia: Mapped[str] = mapped_column(String(300), nullable=False)
    area: Mapped[str] = mapped_column(String(50), nullable=False)
    correo: Mapped[str | None] = mapped_column(String(300), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    documento_id: Mapped[int] = mapped_column(ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[EstadoVersion] = mapped_column(
        Enum(EstadoVersion, name="estado_version_funcionario_enum", values_callable=lambda e: [x.value for x in e]), nullable=False, index=True
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
