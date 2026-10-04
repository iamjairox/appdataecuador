"""Agrega la ciudad pública a las fichas ya consultadas de abogados.

Revision ID: 0014_ciudad_ficha_abogado
Revises: 0013_fichas_abogados
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0014_ciudad_ficha_abogado"
down_revision: str | None = "0013_fichas_abogados"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("abogados_ecuador", sa.Column("ciudad", sa.String(length=150), nullable=True))


def downgrade() -> None:
    op.drop_column("abogados_ecuador", "ciudad")
