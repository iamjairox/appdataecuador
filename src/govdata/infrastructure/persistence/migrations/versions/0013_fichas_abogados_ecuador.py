"""Persiste fichas enriquecidas del directorio Abogados del Ecuador.

Revision ID: 0013_fichas_abogados
Revises: 0012_area_general
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0013_fichas_abogados"
down_revision: str | None = "0012_area_general"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "abogados_ecuador",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("codigo_foro", sa.Integer(), nullable=False, unique=True),
        sa.Column("nombre_completo", sa.String(length=300), nullable=True),
        sa.Column("cedula", sa.String(length=20), nullable=True),
        sa.Column("correo", sa.String(length=320), nullable=True),
        sa.Column("telefono_domicilio", sa.String(length=50), nullable=True),
        sa.Column("direccion_domicilio", sa.String(length=500), nullable=True),
        sa.Column("telefono_oficina", sa.String(length=50), nullable=True),
        sa.Column("direccion_oficina", sa.String(length=500), nullable=True),
        sa.Column("celular", sa.String(length=50), nullable=True),
        sa.Column("consultado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_abogados_ecuador_codigo_foro", "abogados_ecuador", ["codigo_foro"])


def downgrade() -> None:
    op.drop_index("ix_abogados_ecuador_codigo_foro", table_name="abogados_ecuador")
    op.drop_table("abogados_ecuador")
