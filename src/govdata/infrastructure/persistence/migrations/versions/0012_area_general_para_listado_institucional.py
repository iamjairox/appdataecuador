"""Conserva funcionarios no especializados en el listado institucional.

Revision ID: 0012_area_general
Revises: 0011_contactos_foro_y_extension
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op


revision: str = "0012_area_general"
down_revision: str | None = "0011_contactos_foro_y_extension"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE area_relevante_enum ADD VALUE IF NOT EXISTS 'general'")


def downgrade() -> None:
    # PostgreSQL no permite eliminar un valor de ENUM sin recrear el tipo.
    # Se deja para preservar de forma segura los registros ya clasificados.
    pass
