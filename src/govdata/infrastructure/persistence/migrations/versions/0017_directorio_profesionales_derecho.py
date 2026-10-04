"""Directorio local de profesionales del Derecho.

Revision ID: 0017_directorio_profesionales
Revises: 0016_actividad_sri
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_directorio_profesionales"
down_revision: str | None = "0016_actividad_sri"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "directorio_profesionales_derecho",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo_foro", sa.Integer(), nullable=False, unique=True),
        sa.Column("matricula", sa.String(80)),
        sa.Column("nombre_completo", sa.String(350), nullable=False),
        sa.Column("direccion_oficina", sa.String(700)),
        sa.Column("inscripcion", sa.String(150)),
        sa.Column("credencial", sa.String(80)),
        sa.Column("estado", sa.String(100)),
        sa.Column("cargado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_directorio_profesionales_derecho_codigo_foro", "directorio_profesionales_derecho", ["codigo_foro"])
    op.create_index("ix_directorio_profesionales_derecho_nombre_completo", "directorio_profesionales_derecho", ["nombre_completo"])
    op.create_table(
        "estado_directorio_profesionales_derecho",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("total_esperado", sa.Integer()),
        sa.Column("pagina_actual", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("registros_guardados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estado", sa.String(30), nullable=False, server_default="inactivo"),
        sa.Column("mensaje", sa.String(500)),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("estado_directorio_profesionales_derecho")
    op.drop_table("directorio_profesionales_derecho")
