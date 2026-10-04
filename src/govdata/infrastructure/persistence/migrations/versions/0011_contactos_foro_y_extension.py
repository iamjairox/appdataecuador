"""Conserva los contactos del Foro y la extensión institucional.

Revision ID: 0011_contactos_foro_y_extension
Revises: 0010_validacion_abogado_enums
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0011_contactos_foro_y_extension"
down_revision: str | None = "0010_validacion_abogado_enums"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("registro_foro", sa.Column("correo_personal", sa.String(length=320), nullable=True))
    op.add_column("registro_foro", sa.Column("celular_personal", sa.String(length=30), nullable=True))
    op.add_column("personas", sa.Column("extension_telefonica", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("personas", "extension_telefonica")
    op.drop_column("registro_foro", "celular_personal")
    op.drop_column("registro_foro", "correo_personal")
