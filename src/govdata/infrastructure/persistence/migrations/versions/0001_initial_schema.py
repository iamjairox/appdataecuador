"""esquema inicial: entidades, personas, funcionarios, publicaciones,
documentos, historial_cambios, ejecuciones

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-04

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "entidades",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nombre", sa.String(500), nullable=False),
        sa.Column("url_transparencia", sa.String(1000), nullable=False, unique=True),
        sa.Column("portal_origen", sa.String(50), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_extra", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_entidades_portal_origen", "entidades", ["portal_origen"])

    op.create_table(
        "personas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nombres", sa.String(200), nullable=False),
        sa.Column("apellidos", sa.String(200), nullable=False),
        sa.Column("cedula", sa.String(20), nullable=True, unique=True),
        sa.Column("correo", sa.String(320), nullable=True),
        sa.Column("telefono", sa.String(20), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "publicaciones",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("mes_publicado", sa.Date(), nullable=False),
        sa.Column("url_item", sa.String(1000), nullable=False),
        sa.Column("detectado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("entidad_id", "mes_publicado", name="uq_publicacion_entidad_mes"),
    )

    op.create_table(
        "documentos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "publicacion_id",
            sa.Integer(),
            sa.ForeignKey("publicaciones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tipo_archivo",
            sa.Enum("pdf", "xls", "xlsx", name="tipo_archivo_enum"),
            nullable=False,
        ),
        sa.Column("nombre_original", sa.String(500), nullable=False),
        sa.Column("ruta_almacenamiento", sa.String(1000), nullable=False),
        sa.Column("hash_sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("descargado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "funcionarios",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "persona_id", sa.Integer(), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "documento_id",
            sa.Integer(),
            sa.ForeignKey("documentos.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("cargo", sa.String(300), nullable=False),
        sa.Column("dependencia", sa.String(300), nullable=False),
        sa.Column(
            "area_clasificada",
            sa.Enum("juridica", "financiera", name="area_relevante_enum"),
            nullable=False,
        ),
        sa.Column("score_clasificacion", sa.Float(), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=True),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_funcionario_persona_entidad", "funcionarios", ["persona_id", "entidad_id"])
    op.create_index("ix_funcionario_vigente", "funcionarios", ["entidad_id", "fecha_fin"])

    op.create_table(
        "historial_cambios",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "persona_id", sa.Integer(), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "funcionario_id",
            sa.Integer(),
            sa.ForeignKey("funcionarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("campo_modificado", sa.String(100), nullable=False),
        sa.Column("valor_anterior", sa.Text(), nullable=True),
        sa.Column("valor_nuevo", sa.Text(), nullable=True),
        sa.Column("detectado_en", sa.Date(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "ejecuciones",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("etapa", sa.String(100), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("mensaje_error", sa.Text(), nullable=True),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalizado_en", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ejecuciones")
    op.drop_table("historial_cambios")
    op.drop_table("funcionarios")
    op.drop_table("documentos")
    op.drop_table("publicaciones")
    op.drop_table("personas")
    op.drop_table("entidades")
    sa.Enum(name="area_relevante_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_archivo_enum").drop(op.get_bind(), checkfirst=True)
