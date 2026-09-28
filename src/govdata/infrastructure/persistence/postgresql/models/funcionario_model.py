"""Modelo ORM: funcionarios (vinculo Persona-Entidad-Cargo, con vigencia)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.infrastructure.persistence.postgresql.models.base import Base


class FuncionarioModel(Base):
    __tablename__ = "funcionarios"
    __table_args__ = (
        Index("ix_funcionario_persona_entidad", "persona_id", "entidad_id"),
        Index("ix_funcionario_vigente", "entidad_id", "fecha_fin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id", ondelete="CASCADE"), nullable=False)
    entidad_id: Mapped[int] = mapped_column(ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False)
    documento_id: Mapped[int | None] = mapped_column(
        ForeignKey("documentos.id", ondelete="SET NULL"), nullable=True
    )
    cargo: Mapped[str] = mapped_column(String(300), nullable=False)
    dependencia: Mapped[str] = mapped_column(String(300), nullable=False)
    area_clasificada: Mapped[AreaRelevante] = mapped_column(
        Enum(AreaRelevante, name="area_relevante_enum", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    score_clasificacion: Mapped[float | None] = mapped_column(Float, nullable=True)
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
