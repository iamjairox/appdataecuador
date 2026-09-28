"""documentos: soporta ciclo de vida descubierto->descargado, agrega tipo CSV

Revision ID: 0002_documento_descubrimiento
Revises: 0001_initial_schema
Create Date: 2026-08-11

Contexto (Modulo 2 -- Adaptador DPE): el descubrimiento de un documento ya
no implica descargarlo. `documentos` pasa a admitir un estado intermedio
"descubierto" (solo se conoce `url_documento`); `ruta_almacenamiento` y
`hash_sha256` quedan nullable y se completan en el Modulo 3 (descarga).
Tambien se agrega el valor 'csv' al enum de tipo de archivo: se verifico
contra el portal real que "Conjunto de datos" se publica en ese formato
ademas de PDF/XLS/XLSX.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_documento_descubrimiento"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE no puede correr dentro de una transaccion en
    # versiones antiguas de PostgreSQL; se ejecuta en autocommit explicito.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE tipo_archivo_enum ADD VALUE IF NOT EXISTS 'csv'")

    op.add_column(
        "documentos", sa.Column("url_documento", sa.String(1500), nullable=False, server_default="")
    )
    op.alter_column("documentos", "url_documento", server_default=None)

    op.add_column(
        "documentos",
        sa.Column("descubierto_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.alter_column("documentos", "ruta_almacenamiento", existing_type=sa.String(1000), nullable=True)
    op.alter_column("documentos", "hash_sha256", existing_type=sa.String(64), nullable=True)
    op.alter_column(
        "documentos", "descargado_en", existing_type=sa.DateTime(timezone=True), nullable=True, server_default=None
    )

    op.create_unique_constraint("uq_documento_publicacion", "documentos", ["publicacion_id"])


def downgrade() -> None:
    op.drop_constraint("uq_documento_publicacion", "documentos", type_="unique")
    op.alter_column("documentos", "descargado_en", existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column("documentos", "hash_sha256", existing_type=sa.String(64), nullable=False)
    op.alter_column("documentos", "ruta_almacenamiento", existing_type=sa.String(1000), nullable=False)
    op.drop_column("documentos", "descubierto_en")
    op.drop_column("documentos", "url_documento")
    # Nota: PostgreSQL no soporta remover un valor de un enum sin recrearlo;
    # el downgrade deliberadamente deja 'csv' en tipo_archivo_enum.
