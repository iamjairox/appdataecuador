"""Modelo ORM: personas.

Identidad unica de un individuo, independiente de la fuente/entidad. La
deduplicacion entre fuentes se resuelve antes de llegar aqui (Motor de
Identity Resolution, modulo posterior); este modelo solo persiste.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class PersonaModel(Base):
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombres: Mapped[str] = mapped_column(String(200), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(200), nullable=False)
    cedula: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    correo: Mapped[str | None] = mapped_column(String(320), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    extension_telefonica: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    fingerprint_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
