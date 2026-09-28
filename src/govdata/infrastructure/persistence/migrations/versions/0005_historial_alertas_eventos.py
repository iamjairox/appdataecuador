"""Modulo 5: historial de versiones, alertas, eventos, verificaciones,
auditoria de comparacion, oportunidades comerciales

Revision ID: 0005_historial_alertas_eventos
Revises: 0004_job_manager_fingerprint
Create Date: 2026-08-05

Contexto:
  - `versiones_funcionario` (Submodulos 5.2-5.4): historial append-only
    del vinculo Persona-Entidad-Cargo -- nunca se sobreescribe, cada
    cambio real cierra la version vigente y abre la siguiente.
  - `alertas` (Submodulo 5.6) y `oportunidades_comerciales` (Submodulo
    5.17): eventos de negocio estructurados, con UUID como PK (igual que
    `jobs` del Modulo 4).
  - `eventos` (Submodulo 5.7): cola PENDIENTE -> CONSUMIDO -> PROCESADO,
    preparacion para un futuro consumidor externo (n8n/Dashboard/API).
  - `verificaciones` (Submodulos 5.10/5.15): historial de CADA chequeo
    del Motor de Monitoreo Continuo, incluso cuando no hubo cambios.
  - `auditorias_comparacion` (Submodulo 5.9): una fila por ejecucion del
    Motor de Comparacion.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_historial_alertas_eventos"
down_revision: str | None = "0004_job_manager_fingerprint"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ESTADOS_VERSION = ("vigente", "cerrada")
_TIPOS_ALERTA = (
    "nuevo_director_juridico",
    "nuevo_director_financiero",
    "nuevo_procurador",
    "nuevo_abogado",
    "funcionario_eliminado",
    "cambio_correo",
    "cambio_dependencia",
    "cambio_cargo",
    "cambio_masivo",
    "cambio_superior_30_porciento",
    "documento_vacio",
    "documento_sospechoso",
)
_ESTADOS_ALERTA = ("pendiente", "enviada", "descartada")
_NIVELES_CRITICIDAD = ("critico", "alto", "medio", "bajo")
_TIPOS_EVENTO = ("alerta", "oportunidad_comercial")
_ESTADOS_EVENTO = ("pendiente", "consumido", "procesado")
_TIPOS_OPORTUNIDAD = (
    "nuevo_director_juridico",
    "nuevo_procurador",
    "nuevo_director_financiero",
    "cambio_maxima_autoridad_juridica",
    "cambio_masivo_funcionarios",
)


def upgrade() -> None:
    estado_version_enum = postgresql.ENUM(*_ESTADOS_VERSION, name="estado_version_funcionario_enum", create_type=False)
    estado_version_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "versiones_funcionario",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("persona_id", sa.Integer(), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "funcionario_id", sa.Integer(), sa.ForeignKey("funcionarios.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("numero_version", sa.Integer(), nullable=False),
        sa.Column("cargo", sa.String(300), nullable=False),
        sa.Column("dependencia", sa.String(300), nullable=False),
        sa.Column("area", sa.String(50), nullable=False),
        sa.Column("correo", sa.String(300), nullable=True),
        sa.Column("telefono", sa.String(50), nullable=True),
        sa.Column("documento_id", sa.Integer(), sa.ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("estado", estado_version_enum, nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_version_persona_entidad", "versiones_funcionario", ["persona_id", "entidad_id"])
    op.create_index("ix_version_entidad_cargo", "versiones_funcionario", ["entidad_id", "cargo"])
    op.create_index("ix_version_vigente", "versiones_funcionario", ["persona_id", "entidad_id", "estado"])
    op.create_index("ix_versiones_funcionario_estado", "versiones_funcionario", ["estado"])

    tipo_alerta_enum = postgresql.ENUM(*_TIPOS_ALERTA, name="tipo_alerta_enum", create_type=False)
    tipo_alerta_enum.create(op.get_bind(), checkfirst=True)
    estado_alerta_enum = postgresql.ENUM(*_ESTADOS_ALERTA, name="estado_alerta_enum", create_type=False)
    estado_alerta_enum.create(op.get_bind(), checkfirst=True)
    nivel_criticidad_enum = postgresql.ENUM(*_NIVELES_CRITICIDAD, name="nivel_criticidad_enum", create_type=False)
    nivel_criticidad_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "alertas",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False),
        sa.Column("persona_id", sa.Integer(), sa.ForeignKey("personas.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "documento_id", sa.Integer(), sa.ForeignKey("documentos.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("tipo", tipo_alerta_enum, nullable=False),
        sa.Column("prioridad", nivel_criticidad_enum, nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("detectado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", estado_alerta_enum, nullable=False, server_default="pendiente"),
    )
    op.create_index("ix_alerta_entidad", "alertas", ["entidad_id"])
    op.create_index("ix_alerta_documento", "alertas", ["documento_id"])

    tipo_evento_enum = postgresql.ENUM(*_TIPOS_EVENTO, name="tipo_evento_enum", create_type=False)
    tipo_evento_enum.create(op.get_bind(), checkfirst=True)
    estado_evento_enum = postgresql.ENUM(*_ESTADOS_EVENTO, name="estado_evento_enum", create_type=False)
    estado_evento_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "eventos",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tipo", tipo_evento_enum, nullable=False),
        sa.Column("entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referencia_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("estado", estado_evento_enum, nullable=False, server_default="pendiente"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumido_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("procesado_en", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_evento_estado", "eventos", ["estado"])

    op.create_table(
        "verificaciones",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "documento_id", sa.Integer(), sa.ForeignKey("documentos.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("hubo_cambio", sa.Boolean(), nullable=False),
        sa.Column("motivo", sa.String(200), nullable=False),
        sa.Column("hash_verificado", sa.String(64), nullable=True),
        sa.Column("verificado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_verificacion_entidad", "verificaciones", ["entidad_id", "verificado_en"])

    op.create_table(
        "auditorias_comparacion",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False),
        sa.Column("documento_id", sa.Integer(), sa.ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_documento", sa.Integer(), nullable=False),
        sa.Column("ejecutado_por", sa.String(200), nullable=False),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duracion_segundos", sa.Float(), nullable=True),
        sa.Column("cambios_detectados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errores", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_auditoria_documento", "auditorias_comparacion", ["documento_id"])

    tipo_oportunidad_enum = postgresql.ENUM(*_TIPOS_OPORTUNIDAD, name="tipo_oportunidad_enum", create_type=False)
    tipo_oportunidad_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "oportunidades_comerciales",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("entidad_id", sa.Integer(), sa.ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False),
        sa.Column("persona_id", sa.Integer(), sa.ForeignKey("personas.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tipo", tipo_oportunidad_enum, nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("detectado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("prioridad", nivel_criticidad_enum, nullable=False),
    )
    op.create_index("ix_oportunidad_entidad", "oportunidades_comerciales", ["entidad_id"])


def downgrade() -> None:
    op.drop_table("oportunidades_comerciales")
    sa.Enum(name="tipo_oportunidad_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("auditorias_comparacion")
    op.drop_table("verificaciones")

    op.drop_table("eventos")
    sa.Enum(name="estado_evento_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_evento_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("alertas")
    sa.Enum(name="nivel_criticidad_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="estado_alerta_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_alerta_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("versiones_funcionario")
    sa.Enum(name="estado_version_funcionario_enum").drop(op.get_bind(), checkfirst=True)
