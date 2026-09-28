"""Modelo ORM: manifests."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class ManifestModel(Base):
    __tablename__ = "manifests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    documento_id: Mapped[int] = mapped_column(
        ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(1500), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mime: Mapped[str] = mapped_column(String(200), nullable=False)
    bytes_totales: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1500), nullable=False)
    fecha_descarga: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
