"""Modulo 8: Motor de Consulta al Foro de Abogados, Fusion de Datos y
Perfil Consolidado del Funcionario

Revision ID: 0008_foro_abogados
Revises: 0007_senescyt_academico
Create Date: 2026-08-06

Contexto:
  - `consulta_foro` (Submodulo 8.17): auditoria de CADA intento de
    consulta al Foro de Abogados (exitoso o no), con los campos de
    deteccion propios de un scraper HTML tolerante (`codigo_http`,
    `captcha_detectado`, `pagina_vacia`, Submodulo 8.2). Se crea PRIMERO
    porque `registro_foro_version` y `historial_foro` referencian su `id`
    como "origen" del cambio.
  - `registro_foro` (Submodulo 8.1): puntero VIGENTE de una matricula por
    PersonaMaster, incluye metadatos de confiabilidad por fuente (mismo
    patron que `titulo_academico`, Modulo 7).
  - `registro_foro_version` (Submodulos 8.6/8.14): historial append-only,
    "nunca eliminar informacion previa".
  - `historial_foro` (Submodulo 8.6): bitacora de cambios, campo a campo.
  - `evento_foro` (Submodulo 8.7) y `alerta_foro` (Submodulo 8.7): colas
    de eventos/alertas estructurados, mismo patron que
    `evento_academico`/`alerta_academica` (Modulo 7).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_foro_abogados"
down_revision: str | None = "0007_senescyt_academico"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ESTADOS_REGISTRO_FORO = ("vigente", "suspendido", "anulado", "desconocido")
_ESTADOS_VERSION_FORO = ("vigente", "cerrada")
_TIPOS_CAMBIO_FORO = ("dato_nuevo", "dato_eliminado", "cambio_estado", "cambio_provincia", "cambio_registro", "cambio_dato", "sin_cambios")
_TIPOS_EVENTO_FORO = (
    "registro_nuevo", "registro_eliminado", "cambio_estado", "cambio_provincia", "cambio_registro", "cambio_dato",
    "consulta_exitosa", "consulta_fallida",
)
_ESTADOS_EVENTO_FORO = ("pendiente", "consumido", "procesado")
_TIPOS_ALERTA_FORO = ("registro_nuevo", "registro_eliminado", "cambio_estado", "cambio_provincia", "cambio_registro", "cambio_dato")
_ESTADOS_ALERTA_FORO = ("pendiente", "enviada", "descartada")
# "nivel_criticidad_enum" ya existe (Migracion 0005) -- se reutiliza tal
# cual para `alerta_foro.prioridad` (mismo patron que Migracion 0007).


def upgrade() -> None:
    op.create_table(
        "consulta_foro",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exito", sa.Boolean(), nullable=True),
        sa.Column("duracion_segundos", sa.Float(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("reintentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_utilizado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("version_resultante", sa.Integer(), nullable=True),
        sa.Column("respuesta_cruda", sa.JSON(), nullable=True),
        sa.Column("codigo_http", sa.Integer(), nullable=True),
        sa.Column("captcha_detectado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pagina_vacia", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("usuario", sa.String(100), nullable=False, server_default="sistema"),
        sa.Column("job_id", sa.String(36), nullable=True),
    )
    op.create_index("ix_consulta_foro_persona_master", "consulta_foro", ["persona_master_id", "iniciado_en"])

    estado_registro_foro_enum = postgresql.ENUM(*_ESTADOS_REGISTRO_FORO, name="estado_registro_foro_enum", create_type=False)
    estado_registro_foro_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "registro_foro",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clave_registro", sa.String(200), nullable=False),
        sa.Column("nombre_completo", sa.String(300), nullable=True),
        sa.Column("registro", sa.String(100), nullable=True),
        sa.Column("provincia", sa.String(100), nullable=True),
        sa.Column("estado", estado_registro_foro_enum, nullable=False, server_default="desconocido"),
        sa.Column("cedula", sa.String(20), nullable=True),
        sa.Column("numero_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("vigente", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("fuente", sa.String(50), nullable=False, server_default="foro_abogados"),
        sa.Column("fecha_consulta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("nivel_confianza", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("version_fuente", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("evidencia", sa.String(100), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_registro_foro_persona_master", "registro_foro", ["persona_master_id"])
    op.create_index("ix_registro_foro_clave", "registro_foro", ["persona_master_id", "clave_registro", "vigente"])

    estado_version_foro_enum = postgresql.ENUM(*_ESTADOS_VERSION_FORO, name="estado_version_foro_enum", create_type=False)
    estado_version_foro_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "registro_foro_version",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clave_registro", sa.String(200), nullable=False),
        sa.Column("numero_version", sa.Integer(), nullable=False),
        sa.Column("nombre_completo", sa.String(300), nullable=True),
        sa.Column("registro", sa.String(100), nullable=True),
        sa.Column("provincia", sa.String(100), nullable=True),
        sa.Column("estado", estado_registro_foro_enum, nullable=False, server_default="desconocido"),
        sa.Column("cedula", sa.String(20), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("estado_version", estado_version_foro_enum, nullable=False, server_default="vigente"),
        sa.Column("consulta_foro_id", sa.Integer(), sa.ForeignKey("consulta_foro.id", ondelete="CASCADE"), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_registro_foro_version_persona_master", "registro_foro_version", ["persona_master_id", "clave_registro"])
    op.create_index("ix_registro_foro_version_vigente", "registro_foro_version", ["persona_master_id", "clave_registro", "estado_version"])

    tipo_cambio_foro_enum = postgresql.ENUM(*_TIPOS_CAMBIO_FORO, name="tipo_cambio_foro_enum", create_type=False)
    tipo_cambio_foro_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "historial_foro",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clave_registro", sa.String(200), nullable=False),
        sa.Column("tipo_cambio", tipo_cambio_foro_enum, nullable=False),
        sa.Column("detectado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consulta_foro_id", sa.Integer(), sa.ForeignKey("consulta_foro.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ejecutado_por", sa.String(100), nullable=False, server_default="sistema"),
        sa.Column("registro_foro_id", sa.Integer(), sa.ForeignKey("registro_foro.id", ondelete="SET NULL"), nullable=True),
        sa.Column("campos_modificados", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("descripcion", sa.Text(), nullable=True),
    )
    op.create_index("ix_historial_foro_persona_master", "historial_foro", ["persona_master_id"])

    tipo_evento_foro_enum = postgresql.ENUM(*_TIPOS_EVENTO_FORO, name="tipo_evento_foro_enum", create_type=False)
    tipo_evento_foro_enum.create(op.get_bind(), checkfirst=True)
    estado_evento_foro_enum = postgresql.ENUM(*_ESTADOS_EVENTO_FORO, name="estado_evento_foro_enum", create_type=False)
    estado_evento_foro_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "evento_foro",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tipo", tipo_evento_foro_enum, nullable=False),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("estado", estado_evento_foro_enum, nullable=False, server_default="pendiente"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumido_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("procesado_en", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_evento_foro_estado", "evento_foro", ["estado"])
    op.create_index("ix_evento_foro_persona_master", "evento_foro", ["persona_master_id"])

    tipo_alerta_foro_enum = postgresql.ENUM(*_TIPOS_ALERTA_FORO, name="tipo_alerta_foro_enum", create_type=False)
    tipo_alerta_foro_enum.create(op.get_bind(), checkfirst=True)
    estado_alerta_foro_enum = postgresql.ENUM(*_ESTADOS_ALERTA_FORO, name="estado_alerta_foro_enum", create_type=False)
    estado_alerta_foro_enum.create(op.get_bind(), checkfirst=True)
    nivel_criticidad_enum = postgresql.ENUM("critico", "alto", "medio", "bajo", name="nivel_criticidad_enum", create_type=False)
    nivel_criticidad_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "alerta_foro",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", tipo_alerta_foro_enum, nullable=False),
        sa.Column("prioridad", nivel_criticidad_enum, nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("detectado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", estado_alerta_foro_enum, nullable=False, server_default="pendiente"),
        sa.Column("registro_foro_id", sa.Integer(), sa.ForeignKey("registro_foro.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_alerta_foro_persona_master", "alerta_foro", ["persona_master_id"])
    op.create_index("ix_alerta_foro_estado", "alerta_foro", ["estado"])


def downgrade() -> None:
    op.drop_table("alerta_foro")
    sa.Enum(name="estado_alerta_foro_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_alerta_foro_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("evento_foro")
    sa.Enum(name="estado_evento_foro_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_evento_foro_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("historial_foro")
    sa.Enum(name="tipo_cambio_foro_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("registro_foro_version")
    sa.Enum(name="estado_version_foro_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("registro_foro")
    sa.Enum(name="estado_registro_foro_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("consulta_foro")
