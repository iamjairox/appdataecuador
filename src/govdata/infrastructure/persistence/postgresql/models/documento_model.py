"""Modelo ORM: documentos."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.entities.documento import EstadoDocumento, TipoArchivo
from govdata.infrastructure.persistence.postgresql.models.base import Base


class DocumentoModel(Base):
    __tablename__ = "documentos"
    __table_args__ = (
        # Dentro del alcance actual (descubrimiento), una publicacion mensual
        # tiene a lo sumo un documento de interes (el directorio de personal).
        UniqueConstraint("publicacion_id", name="uq_documento_publicacion"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    publicacion_id: Mapped[int] = mapped_column(
        ForeignKey("publicaciones.id", ondelete="CASCADE"), nullable=False
    )
    tipo_archivo: Mapped[TipoArchivo] = mapped_column(
        Enum(TipoArchivo, name="tipo_archivo_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    estado: Mapped[EstadoDocumento] = mapped_column(
        Enum(EstadoDocumento, name="estado_documento_enum", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoDocumento.DESCUBIERTO,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    nombre_original: Mapped[str] = mapped_column(String(500), nullable=False)
    url_documento: Mapped[str] = mapped_column(String(1500), nullable=False)
    etag: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tamano_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ruta_almacenamiento: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    hash_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    descubierto_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    descargado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
