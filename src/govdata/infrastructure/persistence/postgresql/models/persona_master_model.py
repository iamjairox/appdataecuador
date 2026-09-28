"""Modelo ORM: personas_master (Submodulo 6.1, Master Person)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.estado_persona_master import EstadoPersonaMaster
from govdata.infrastructure.persistence.postgresql.models.base import Base


class PersonaMasterModel(Base):
    __tablename__ = "personas_master"
    __table_args__ = (
        Index("ix_persona_master_fingerprint", "fingerprint_principal"),
        Index("ix_persona_master_fingerprint_fonetico", "fingerprint_fonetico"),
        Index("ix_persona_master_correo", "correo_principal"),
        Index("ix_persona_master_estado", "estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, default=uuid.uuid4, unique=True)
    persona_id: Mapped[int] = mapped_column(
        ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    nombres: Mapped[str] = mapped_column(String(200), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(200), nullable=False)
    fingerprint_principal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fingerprint_fonetico: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sexo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    correo_principal: Mapped[str | None] = mapped_column(String(320), nullable=True)
    telefono_principal: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estado: Mapped[EstadoPersonaMaster] = mapped_column(
        Enum(EstadoPersonaMaster, name="estado_persona_master_enum", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoPersonaMaster.ACTIVA,
    )
    nivel_confianza: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    cantidad_fuentes: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cantidad_cargos_historicos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fusionada_en_id: Mapped[int | None] = mapped_column(
        ForeignKey("personas_master.id", ondelete="SET NULL"), nullable=True
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
