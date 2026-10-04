"""Directorio local Supercias y representante individual.

Revision ID: 0015_directorio_companias
Revises: 0014_ciudad_ficha_abogado
"""
from __future__ import annotations
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "0015_directorio_companias"
down_revision: str | None = "0014_ciudad_ficha_abogado"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table("companias_supercias", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("ruc", sa.String(20), nullable=False, unique=True), sa.Column("expediente", sa.String(40)), sa.Column("nombre", sa.String(600), nullable=False), sa.Column("situacion_legal", sa.String(250)), sa.Column("provincia", sa.String(120)), sa.Column("canton", sa.String(120)), sa.Column("ciudad", sa.String(120)), sa.Column("direccion", sa.String(1000)), sa.Column("telefono", sa.String(80)), sa.Column("representante", sa.String(350)), sa.Column("cargo_representante", sa.String(300)), sa.Column("ciiu_nivel_1", sa.String(30)), sa.Column("ciiu_nivel_6", sa.String(50)), sa.Column("es_juridica", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("periodo_fuente", sa.String(40)), sa.Column("cargado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_companias_supercias_ruc", "companias_supercias", ["ruc"])
    op.create_index("ix_companias_supercias_nombre", "companias_supercias", ["nombre"])
    op.create_index("ix_companias_supercias_es_juridica", "companias_supercias", ["es_juridica"])
    op.create_table("representantes_companias", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("compania_id", sa.Integer(), sa.ForeignKey("companias_supercias.id", ondelete="CASCADE"), nullable=False, unique=True), sa.Column("nombre", sa.String(350), nullable=False), sa.Column("cedula", sa.String(20)), sa.Column("correo", sa.String(320)), sa.Column("celular", sa.String(50)), sa.Column("telefono_domicilio", sa.String(80)), sa.Column("telefono_oficina", sa.String(80)), sa.Column("direccion_domicilio", sa.String(1000)), sa.Column("direccion_oficina", sa.String(1000)), sa.Column("estado", sa.String(80), nullable=False, server_default="pendiente"), sa.Column("consultado_en", sa.DateTime(timezone=True)))

def downgrade() -> None:
    op.drop_table("representantes_companias")
    op.drop_table("companias_supercias")
