"""Modelo ORM: consulta_foro (Submodulo 8.17, auditoria)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class ConsultaForoModel(Base):
    __tablename__ = "consulta_foro"
    __table_args__ = (Index("ix_consulta_foro_persona_master", "persona_master_id", "iniciado_en"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_master_id: Mapped[int] = mapped_column(
        ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False
    )
    iniciado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exito: Mapped[bool | None] = mapped_column(nullable=True)
    duracion_segundos: Mapped[float | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    reintentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_utilizado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version_resultante: Mapped[int | None] = mapped_column(Integer, nullable=True)
    respuesta_cruda: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    codigo_http: Mapped[int | None] = mapped_column(Integer, nullable=True)
    captcha_detectado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pagina_vacia: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    usuario: Mapped[str] = mapped_column(String(100), nullable=False, default="sistema")
    job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
