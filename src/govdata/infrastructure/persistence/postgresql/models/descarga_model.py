"""Modelo ORM: descargas."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.entities.descarga import EstadoDescarga
from govdata.infrastructure.persistence.postgresql.models.base import Base


class DescargaModel(Base):
    __tablename__ = "descargas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    documento_id: Mapped[int] = mapped_column(
        ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    numero_intento: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[EstadoDescarga] = mapped_column(
        Enum(EstadoDescarga, name="estado_descarga_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    codigo_http: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type_recibido: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tamano_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hash_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    velocidad_bytes_por_segundo: Mapped[float | None] = mapped_column(Float, nullable=True)
    mensaje_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    iniciado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
