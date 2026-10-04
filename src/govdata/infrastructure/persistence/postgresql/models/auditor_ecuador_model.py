from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.infrastructure.persistence.postgresql.models.base import Base


class AuditorEcuadorModel(Base):
    __tablename__ = "auditores_ecuador"

    id: Mapped[int] = mapped_column(primary_key=True)
    rnae: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    identificacion: Mapped[str] = mapped_column(String(20), index=True)
    nombre: Mapped[str] = mapped_column(String(350), index=True)
    resolucion: Mapped[str | None] = mapped_column(String(80))
    fecha_resolucion: Mapped[str | None] = mapped_column(String(40))
    nacionalidad: Mapped[str | None] = mapped_column(String(80))
    provincia: Mapped[str | None] = mapped_column(String(100))
    canton: Mapped[str | None] = mapped_column(String(100))
    direccion: Mapped[str | None] = mapped_column(String(1000))
    telefono: Mapped[str | None] = mapped_column(String(80))
    correo: Mapped[str | None] = mapped_column(String(320))
    cargado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
