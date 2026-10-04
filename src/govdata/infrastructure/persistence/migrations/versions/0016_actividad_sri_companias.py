"""Persist activity obtained by individual SRI company lookup.

Revision ID: 0016_actividad_sri
Revises: 0015_directorio_companias
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_actividad_sri"
down_revision: str | None = "0015_directorio_companias"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("representantes_companias", sa.Column("actividad_economica", sa.String(2000), nullable=True))


def downgrade() -> None:
    op.drop_column("representantes_companias", "actividad_economica")
