"""Modulo 4: fingerprint en personas, tablas jobs y job_steps

Revision ID: 0004_job_manager_fingerprint
Revises: 0003_descarga_manifest_version
Create Date: 2026-08-05

Contexto:
  - `personas` gana `fingerprint`/`fingerprint_hash` (Submodulo 4.4,
    Identity Resolution primera etapa -- solo se almacena, no se compara
    todavia).
  - `jobs`/`job_steps` (Submodulo 4.8, Job Manager): auditoria y
    seguimiento de cada consulta end-to-end.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_job_manager_fingerprint"
down_revision: str | None = "0003_descarga_manifest_version"  # ID acortado, ver 0003
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ESTADOS_JOB = (
    "pendiente",
    "en_cola",
    "descubriendo",
    "descargando",
    "extrayendo",
    "normalizando",
    "clasificando",
    "guardando",
    "consultando_senescyt",
    "consultando_foro",
    "finalizado",
    "error",
)
_TIPOS_JOB = ("consulta_individual", "consulta_masiva", "consulta_filtros")


def upgrade() -> None:
    op.add_column("personas", sa.Column("fingerprint", sa.String(500), nullable=True))
    op.add_column("personas", sa.Column("fingerprint_hash", sa.String(64), nullable=True))
    op.create_index("ix_personas_fingerprint", "personas", ["fingerprint"])
    op.create_index("ix_personas_fingerprint_hash", "personas", ["fingerprint_hash"])

    job_status_enum = postgresql.ENUM(*_ESTADOS_JOB, name="job_status_enum", create_type=False)
    job_status_enum.create(op.get_bind(), checkfirst=True)
    tipo_job_enum = postgresql.ENUM(*_TIPOS_JOB, name="tipo_job_enum", create_type=False)
    tipo_job_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tipo", tipo_job_enum, nullable=False),
        sa.Column(
            "entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("estado", job_status_enum, nullable=False),
        sa.Column("porcentaje", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("errores", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("reintentos", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_jobs_estado", "jobs", ["estado"])

    op.create_table(
        "job_steps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("estado", job_status_enum, nullable=False),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mensaje", sa.Text(), nullable=True),
    )
    op.create_index("ix_job_steps_job_id", "job_steps", ["job_id"])


def downgrade() -> None:
    op.drop_table("job_steps")
    op.drop_table("jobs")
    sa.Enum(name="tipo_job_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="job_status_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_personas_fingerprint_hash", table_name="personas")
    op.drop_index("ix_personas_fingerprint", table_name="personas")
    op.drop_column("personas", "fingerprint_hash")
    op.drop_column("personas", "fingerprint")
