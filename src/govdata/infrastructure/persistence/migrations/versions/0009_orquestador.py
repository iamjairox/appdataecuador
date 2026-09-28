"""Modulo 9: Orquestador Maestro del Sistema GovData

Revision ID: 0009_orquestador
Revises: 0008_foro_abogados
Create Date: 2026-08-06

Contexto:
  - `trabajo_orquestador` (Submodulos 9.6/9.7/9.8): cola de trabajos
    persistida en PostgreSQL (NUNCA Redis), con `version_lock` para
    bloqueo optimista.
  - `auditoria_etapa` (Submodulos 9.10/9.15): una fila por PASO del
    Planificador ejecutado/omitido/fallido para un `trabajo_orquestador`.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_orquestador"
down_revision: str | None = "0008_foro_abogados"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TIPOS_TRABAJO = (
    "consulta_entidad", "consulta_masiva", "consulta_filtro", "actualizacion_entidad", "actualizacion_masiva",
    "reproceso",
)
_ESTADOS_TRABAJO = (
    "pendiente", "en_cola", "ejecutando", "pausado", "reintentando", "completado", "cancelado", "error",
)
_NIVELES_PRIORIDAD = ("muy_alta", "alta", "media", "baja")
_TIPOS_PASO = ("descubrimiento", "descarga", "extraccion", "senescyt", "foro", "comparacion", "perfil", "alertas")
_ESTADOS_PASO = ("ejecutado", "omitido", "fallido")


def upgrade() -> None:
    tipo_trabajo_enum = postgresql.ENUM(*_TIPOS_TRABAJO, name="tipo_trabajo_orquestador_enum", create_type=False)
    tipo_trabajo_enum.create(op.get_bind(), checkfirst=True)
    estado_trabajo_enum = postgresql.ENUM(*_ESTADOS_TRABAJO, name="estado_trabajo_orquestador_enum", create_type=False)
    estado_trabajo_enum.create(op.get_bind(), checkfirst=True)
    nivel_prioridad_enum = postgresql.ENUM(*_NIVELES_PRIORIDAD, name="nivel_prioridad_ejecucion_enum", create_type=False)
    nivel_prioridad_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "trabajo_orquestador",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tipo", tipo_trabajo_enum, nullable=False),
        sa.Column("parametros", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("politica", sa.String(100), nullable=False, server_default="consulta_rapida"),
        sa.Column("estado", estado_trabajo_enum, nullable=False, server_default="pendiente"),
        sa.Column("prioridad", nivel_prioridad_enum, nullable=False, server_default="media"),
        sa.Column("version_lock", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_intentos", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="SET NULL"), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_error", sa.Text(), nullable=True),
    )
    op.create_index("ix_trabajo_orquestador_estado", "trabajo_orquestador", ["estado"])
    op.create_index("ix_trabajo_orquestador_estado_prioridad", "trabajo_orquestador", ["estado", "prioridad"])
    op.create_index("ix_trabajo_orquestador_entidad", "trabajo_orquestador", ["entidad_id"])

    tipo_paso_enum = postgresql.ENUM(*_TIPOS_PASO, name="tipo_paso_pipeline_enum", create_type=False)
    tipo_paso_enum.create(op.get_bind(), checkfirst=True)
    estado_paso_enum = postgresql.ENUM(*_ESTADOS_PASO, name="estado_paso_enum", create_type=False)
    estado_paso_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "auditoria_etapa",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("trabajo_orquestador_id", sa.Uuid(), sa.ForeignKey("trabajo_orquestador.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo_paso", tipo_paso_enum, nullable=False),
        sa.Column("estado_paso", estado_paso_enum, nullable=False),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("razon_omision", sa.Text(), nullable=True),
        sa.Column("cantidad_registros", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("cache_utilizada", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("version_utilizada", sa.String(100), nullable=True),
    )
    op.create_index("ix_auditoria_etapa_trabajo", "auditoria_etapa", ["trabajo_orquestador_id"])
    op.create_index("ix_auditoria_etapa_tipo_paso", "auditoria_etapa", ["tipo_paso"])


def downgrade() -> None:
    op.drop_table("auditoria_etapa")
    sa.Enum(name="estado_paso_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_paso_pipeline_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("trabajo_orquestador")
    sa.Enum(name="nivel_prioridad_ejecucion_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="estado_trabajo_orquestador_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_trabajo_orquestador_enum").drop(op.get_bind(), checkfirst=True)
