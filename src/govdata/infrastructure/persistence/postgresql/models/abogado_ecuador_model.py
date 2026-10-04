"""Ficha enriquecida de un abogado consultado desde el directorio nacional."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class AbogadoEcuadorModel(Base):
    __tablename__ = "abogados_ecuador"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo_foro: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    nombre_completo: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ciudad: Mapped[str | None] = mapped_column(String(150), nullable=True)
    cedula: Mapped[str | None] = mapped_column(String(20), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(320), nullable=True)
    telefono_domicilio: Mapped[str | None] = mapped_column(String(50), nullable=True)
    direccion_domicilio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    telefono_oficina: Mapped[str | None] = mapped_column(String(50), nullable=True)
    direccion_oficina: Mapped[str | None] = mapped_column(String(500), nullable=True)
    celular: Mapped[str | None] = mapped_column(String(50), nullable=True)
    consultado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
