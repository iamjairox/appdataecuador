"""Modulo 7: Adaptador SENESCYT + Enriquecimiento Academico

Revision ID: 0007_senescyt_academico
Revises: 0006_identidad_maestra
Create Date: 2026-08-06

Contexto:
  - `consulta_senescyt` (Submodulo 7.15): auditoria de CADA intento de
    consulta a SENESCYT (exitoso o no), con respuesta cruda para
    trazabilidad. Se crea PRIMERO porque `titulo_version` y
    `historial_academico` referencian su `id` como "origen" del cambio.
  - `titulo_academico` (Submodulo 7.6): puntero VIGENTE de un titulo por
    PersonaMaster, incluye metadatos de confiabilidad por fuente
    (Submodulo 7.20, mejora 1).
  - `titulo_version` (Submodulos 7.6/7.14): historial append-only,
    "nunca sobrescribir".
  - `historial_academico` (Submodulo 7.14): bitacora de cambios,
    campo a campo.
  - `evento_academico` (Submodulo 7.9) y `alerta_academica` (Submodulo
    7.8): colas de eventos/alertas estructurados, mismo patron que
    `eventos_perfil`/`alertas_perfil` (Modulo 6).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_senescyt_academico"
down_revision: str | None = "0006_identidad_maestra"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ESTADOS_REGISTRO_ACADEMICO = ("vigente", "suspendido", "anulado", "desconocido")
_ESTADOS_VERSION_ACADEMICA = ("vigente", "cerrada")
_TIPOS_CAMBIO_ACADEMICO = (
    "titulo_nuevo", "titulo_eliminado", "cambio_universidad", "cambio_nivel", "cambio_modalidad",
    "cambio_registro", "cambio_estado", "cambio_fecha", "cambio_multiple", "sin_cambios",
)
_TIPOS_EVENTO_ACADEMICO = (
    "titulo_nuevo", "titulo_eliminado", "cambio_nivel", "cambio_universidad", "cambio_estado",
    "consulta_exitosa", "consulta_fallida",
)
_ESTADOS_EVENTO_ACADEMICO = ("pendiente", "consumido", "procesado")
_TIPOS_ALERTA_ACADEMICA = (
    "nuevo_titulo", "titulo_eliminado", "registro_suspendido", "registro_anulado", "cambio_nivel",
    "cambio_institucion", "cambio_estado",
)
_ESTADOS_ALERTA_ACADEMICA = ("pendiente", "enviada", "descartada")
_NIVELES_CRITICIDAD = ("critico", "alto", "medio", "bajo")
# "nivel_criticidad_enum" ya existe (Migracion 0005) -- se reutiliza tal
# cual para `alerta_academica.prioridad` (ver Migracion 0006 para el
# mismo patron de reutilizacion sin recrear el tipo).


def upgrade() -> None:
    op.create_table(
        "consulta_senescyt",
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
    )
    op.create_index("ix_consulta_senescyt_persona_master", "consulta_senescyt", ["persona_master_id", "iniciado_en"])

    estado_registro_enum = postgresql.ENUM(*_ESTADOS_REGISTRO_ACADEMICO, name="estado_registro_academico_enum", create_type=False)
    estado_registro_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "titulo_academico",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clave_titulo", sa.String(200), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("nivel", sa.String(100), nullable=False),
        sa.Column("institucion", sa.String(300), nullable=False),
        sa.Column("fecha_registro", sa.Date(), nullable=True),
        sa.Column("pais", sa.String(100), nullable=True),
        sa.Column("estado", estado_registro_enum, nullable=False, server_default="desconocido"),
        sa.Column("modalidad", sa.String(100), nullable=True),
        sa.Column("numero_registro", sa.String(100), nullable=True),
        sa.Column("area_conocimiento", sa.String(200), nullable=True),
        sa.Column("tipo_titulo", sa.String(100), nullable=True),
        sa.Column("fecha_graduacion", sa.Date(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("numero_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("vigente", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("fuente", sa.String(50), nullable=False, server_default="senescyt"),
        sa.Column("fecha_consulta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("nivel_confianza", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("version_fuente", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("evidencia", sa.String(100), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_titulo_academico_persona_master", "titulo_academico", ["persona_master_id"])
    op.create_index("ix_titulo_academico_clave", "titulo_academico", ["persona_master_id", "clave_titulo", "vigente"])

    estado_version_academica_enum = postgresql.ENUM(*_ESTADOS_VERSION_ACADEMICA, name="estado_version_academica_enum", create_type=False)
    estado_version_academica_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "titulo_version",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clave_titulo", sa.String(200), nullable=False),
        sa.Column("numero_version", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("nivel", sa.String(100), nullable=False),
        sa.Column("institucion", sa.String(300), nullable=False),
        sa.Column("fecha_registro", sa.Date(), nullable=True),
        sa.Column("pais", sa.String(100), nullable=True),
        sa.Column("estado", estado_registro_enum, nullable=False, server_default="desconocido"),
        sa.Column("modalidad", sa.String(100), nullable=True),
        sa.Column("numero_registro", sa.String(100), nullable=True),
        sa.Column("area_conocimiento", sa.String(200), nullable=True),
        sa.Column("tipo_titulo", sa.String(100), nullable=True),
        sa.Column("fecha_graduacion", sa.Date(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("estado_version", estado_version_academica_enum, nullable=False, server_default="vigente"),
        sa.Column("consulta_senescyt_id", sa.Integer(), sa.ForeignKey("consulta_senescyt.id", ondelete="CASCADE"), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_titulo_version_persona_master", "titulo_version", ["persona_master_id", "clave_titulo"])
    op.create_index("ix_titulo_version_vigente", "titulo_version", ["persona_master_id", "clave_titulo", "estado_version"])

    tipo_cambio_academico_enum = postgresql.ENUM(*_TIPOS_CAMBIO_ACADEMICO, name="tipo_cambio_academico_enum", create_type=False)
    tipo_cambio_academico_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "historial_academico",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clave_titulo", sa.String(200), nullable=False),
        sa.Column("tipo_cambio", tipo_cambio_academico_enum, nullable=False),
        sa.Column("detectado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consulta_senescyt_id", sa.Integer(), sa.ForeignKey("consulta_senescyt.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ejecutado_por", sa.String(100), nullable=False, server_default="sistema"),
        sa.Column("titulo_academico_id", sa.Integer(), sa.ForeignKey("titulo_academico.id", ondelete="SET NULL"), nullable=True),
        sa.Column("campos_modificados", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("descripcion", sa.Text(), nullable=True),
    )
    op.create_index("ix_historial_academico_persona_master", "historial_academico", ["persona_master_id"])

    tipo_evento_academico_enum = postgresql.ENUM(*_TIPOS_EVENTO_ACADEMICO, name="tipo_evento_academico_enum", create_type=False)
    tipo_evento_academico_enum.create(op.get_bind(), checkfirst=True)
    estado_evento_academico_enum = postgresql.ENUM(*_ESTADOS_EVENTO_ACADEMICO, name="estado_evento_academico_enum", create_type=False)
    estado_evento_academico_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "evento_academico",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tipo", tipo_evento_academico_enum, nullable=False),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("estado", estado_evento_academico_enum, nullable=False, server_default="pendiente"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumido_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("procesado_en", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_evento_academico_estado", "evento_academico", ["estado"])
    op.create_index("ix_evento_academico_persona_master", "evento_academico", ["persona_master_id"])

    tipo_alerta_academica_enum = postgresql.ENUM(*_TIPOS_ALERTA_ACADEMICA, name="tipo_alerta_academica_enum", create_type=False)
    tipo_alerta_academica_enum.create(op.get_bind(), checkfirst=True)
    estado_alerta_academica_enum = postgresql.ENUM(*_ESTADOS_ALERTA_ACADEMICA, name="estado_alerta_academica_enum", create_type=False)
    estado_alerta_academica_enum.create(op.get_bind(), checkfirst=True)
    nivel_criticidad_enum = postgresql.ENUM(*_NIVELES_CRITICIDAD, name="nivel_criticidad_enum", create_type=False)
    nivel_criticidad_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "alerta_academica",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", tipo_alerta_academica_enum, nullable=False),
        sa.Column("prioridad", nivel_criticidad_enum, nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("detectado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", estado_alerta_academica_enum, nullable=False, server_default="pendiente"),
        sa.Column("titulo_academico_id", sa.Integer(), sa.ForeignKey("titulo_academico.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_alerta_academica_persona_master", "alerta_academica", ["persona_master_id"])
    op.create_index("ix_alerta_academica_estado", "alerta_academica", ["estado"])


def downgrade() -> None:
    op.drop_table("alerta_academica")
    sa.Enum(name="estado_alerta_academica_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_alerta_academica_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("evento_academico")
    sa.Enum(name="estado_evento_academico_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_evento_academico_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("historial_academico")
    sa.Enum(name="tipo_cambio_academico_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("titulo_version")
    sa.Enum(name="estado_version_academica_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("titulo_academico")
    sa.Enum(name="estado_registro_academico_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("consulta_senescyt")
