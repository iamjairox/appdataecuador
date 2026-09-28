"""documentos: maquina de estados + version; nuevas tablas descargas y manifests

Revision ID: 0003_descarga_manifest_version
Revises: 0002_documento_descubrimiento
Create Date: 2026-08-11

Contexto (Modulo 3 -- Descarga de Documentos):

  - `documentos` gana `estado` (maquina de estados DESCUBIERTO/DESCARGANDO/
    DESCARGADO/ERROR/OBSOLETO), `version` (se incrementa cuando una
    redescarga trae un hash distinto -- asi se detecta que el archivo
    publicado cambio sin depender del nombre), `etag`, `last_modified`,
    `tamano_bytes` y `actualizado_en` (usado para liberar documentos
    "estancados" en DESCARGANDO si un worker se cae a mitad de una
    descarga).
  - Se elimina la unicidad de `documentos.hash_sha256`: ya no tiene
    sentido a nivel de "puntero al estado actual" -- la deduplicacion
    GLOBAL por hash ahora vive en la nueva tabla `manifests`.
  - `descargas`: historial append-only de cada intento (exitoso o no).
  - `manifests`: registro canonico append-only de cada version de archivo
    efectivamente almacenada (deduplicacion por `sha256`).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ID acortado (31 -> el original, "0003_descarga_manifest_versionado", tiene
# 33 caracteres y excede el `VARCHAR(32)` por defecto de
# `alembic_version.version_num` -- bug real confirmado corriendo `alembic
# upgrade head` completo: la migracion ejecuta TODO su DDL correctamente y
# recien falla al guardar el numero de revision, revirtiendo todo el
# progreso. FIX autorizado explicitamente por el usuario, misma excepcion
# puntual que el fix del enum de mas abajo).
revision: str = "0003_descarga_manifest_version"
down_revision: str | None = "0002_documento_descubrimiento"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enums nuevos que usan las columnas agregadas mas abajo.
    estado_documento_enum = sa.Enum(
        "descubierto", "descargando", "descargado", "error", "obsoleto", name="estado_documento_enum"
    )
    estado_documento_enum.create(op.get_bind(), checkfirst=True)

    # `postgresql.ENUM(..., create_type=False)`: el tipo ya se crea
    # explicitamente en la linea siguiente (con `checkfirst=True`) -- sin
    # esto, `op.create_table` (mas abajo) vuelve a emitir su propio
    # `CREATE TYPE` implicito para esta misma columna y falla con
    # `DuplicateObject` en una base de datos nueva (bug real, confirmado
    # corriendo `alembic upgrade head` contra un volumen Postgres recien
    # creado). NOTA: `sa.Enum(..., create_type=False)` (el tipo generico,
    # cross-dialect) NO alcanza -- ese kwarg se ignora silenciosamente en
    # SQLAlchemy 2.0 salvo que se use el tipo especifico del dialecto
    # (`sqlalchemy.dialects.postgresql.ENUM`), confirmado reproduciendo
    # ambos casos de forma aislada. FIX autorizado explicitamente por el
    # usuario fuera del alcance normal de fases de frontend, unica
    # excepcion a "src/govdata/ nunca se modifica".
    estado_descarga_enum = postgresql.ENUM("exito", "fallo", name="estado_descarga_enum", create_type=False)
    estado_descarga_enum.create(op.get_bind(), checkfirst=True)

    # documentos: nuevas columnas de estado/version/validadores HTTP.
    op.add_column(
        "documentos",
        sa.Column(
            "estado", estado_documento_enum, nullable=False, server_default="descubierto"
        ),
    )
    op.add_column(
        "documentos", sa.Column("version", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column("documentos", sa.Column("etag", sa.String(200), nullable=True))
    op.add_column("documentos", sa.Column("last_modified", sa.String(100), nullable=True))
    op.add_column("documentos", sa.Column("tamano_bytes", sa.Integer(), nullable=True))
    op.add_column(
        "documentos",
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_documentos_estado", "documentos", ["estado"])
    op.create_index("ix_documentos_hash_sha256", "documentos", ["hash_sha256"])

    # La unicidad de hash_sha256 (creada en 0001 via Column(unique=True))
    # ya no aplica -- el nombre sigue la convencion por defecto de
    # SQLAlchemy/Postgres para `unique=True` en `create_table`.
    op.drop_constraint("documentos_hash_sha256_key", "documentos", type_="unique")

    op.create_table(
        "descargas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "documento_id", sa.Integer(), sa.ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("numero_intento", sa.Integer(), nullable=False),
        sa.Column("estado", estado_descarga_enum, nullable=False),
        sa.Column("codigo_http", sa.Integer(), nullable=True),
        sa.Column("content_type_recibido", sa.String(200), nullable=True),
        sa.Column("tamano_bytes", sa.Integer(), nullable=True),
        sa.Column("hash_sha256", sa.String(64), nullable=True),
        sa.Column("velocidad_bytes_por_segundo", sa.Float(), nullable=True),
        sa.Column("mensaje_error", sa.Text(), nullable=True),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalizado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_descargas_documento_id", "descargas", ["documento_id"])

    op.create_table(
        "manifests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "documento_id", sa.Integer(), sa.ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("url", sa.String(1500), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("mime", sa.String(200), nullable=False),
        sa.Column("bytes_totales", sa.BigInteger(), nullable=False),
        sa.Column("storage_uri", sa.String(1500), nullable=False),
        sa.Column("fecha_descarga", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_manifests_documento_id", "manifests", ["documento_id"])
    op.create_index("ix_manifests_sha256", "manifests", ["sha256"])


def downgrade() -> None:
    op.drop_table("manifests")
    op.drop_table("descargas")

    op.create_unique_constraint("documentos_hash_sha256_key", "documentos", ["hash_sha256"])
    op.drop_index("ix_documentos_hash_sha256", table_name="documentos")
    op.drop_index("ix_documentos_estado", table_name="documentos")
    op.drop_column("documentos", "actualizado_en")
    op.drop_column("documentos", "tamano_bytes")
    op.drop_column("documentos", "last_modified")
    op.drop_column("documentos", "etag")
    op.drop_column("documentos", "version")
    op.drop_column("documentos", "estado")

    sa.Enum(name="estado_descarga_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="estado_documento_enum").drop(op.get_bind(), checkfirst=True)
