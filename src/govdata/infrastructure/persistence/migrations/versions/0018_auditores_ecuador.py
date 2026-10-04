"""Auditores externos personas naturales.

Revision ID: 0018_auditores_ecuador
Revises: 0017_directorio_profesionales
"""
from __future__ import annotations
import sqlalchemy as sa
from alembic import op

revision = "0018_auditores_ecuador"
down_revision = "0017_directorio_profesionales"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("auditores_ecuador", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("rnae", sa.String(30), nullable=False, unique=True), sa.Column("identificacion", sa.String(20), nullable=False), sa.Column("nombre", sa.String(350), nullable=False), sa.Column("resolucion", sa.String(80)), sa.Column("fecha_resolucion", sa.String(40)), sa.Column("nacionalidad", sa.String(80)), sa.Column("provincia", sa.String(100)), sa.Column("canton", sa.String(100)), sa.Column("direccion", sa.String(1000)), sa.Column("telefono", sa.String(80)), sa.Column("correo", sa.String(320)), sa.Column("cargado_en", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_auditores_ecuador_nombre", "auditores_ecuador", ["nombre"])
    op.create_index("ix_auditores_ecuador_identificacion", "auditores_ecuador", ["identificacion"])

def downgrade():
    op.drop_table("auditores_ecuador")
