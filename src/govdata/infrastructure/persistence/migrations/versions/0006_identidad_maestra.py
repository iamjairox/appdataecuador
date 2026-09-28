"""Modulo 6: Motor de Identidad, Enriquecimiento de Personas y Fuentes
Externas

Revision ID: 0006_identidad_maestra
Revises: 0005_historial_alertas_eventos
Create Date: 2026-08-06

Contexto:
  - `personas_master` (Submodulo 6.1): registro maestro unico de
    identidad, 1:1 con `personas` (Modulo 1, congelado) al momento de la
    resolucion inicial; puede terminar apuntando a otra via
    `fusionada_en_id` (Submodulo 6.14/6.21).
  - `registros_fuente` (Submodulo 6.9): snapshot versionado, append-only,
    de cada respuesta de una fuente externa (o DPE) para una PersonaMaster.
  - `atributos_trazables` (Submodulo 6.15): procedencia (quien/cuando/
    fuente/score) de cada campo consolidado.
  - `casos_revision_identidad` (Submodulo 6.21): auditoria de toda
    decision de fusion, automatica o manual.
  - `consultas_fuente_log` (Submodulo 6.10): historial de CADA intento de
    consulta a una fuente, exitoso o no.
  - `eventos_perfil` (Submodulo 6.12) y `alertas_perfil` (Submodulo 6.13):
    equivalentes a `eventos`/`alertas` (Modulo 5) pero sobre el perfil
    consolidado de una Persona, no sobre un Funcionario en una Entidad.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_identidad_maestra"
down_revision: str | None = "0005_historial_alertas_eventos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ESTADOS_PERSONA_MASTER = ("activa", "en_revision", "fusionada")
_FUENTES_EXTERNAS = (
    "dpe",
    "senescyt",
    "foro_abogados",
    "funcion_judicial",
    "sri",
    "contraloria",
    "registro_mercantil",
    "otra",
)
_ESTADOS_REVISION_IDENTIDAD = ("pendiente_revision", "aprobado", "rechazado")
_TIPOS_EVENTO_IDENTIDAD = (
    "persona_enriquecida",
    "persona_fusionada",
    "nueva_fuente",
    "cambio_de_profesion",
    "nuevo_titulo",
    "fuente_actualizada",
)
_ESTADOS_EVENTO_PERFIL = ("pendiente", "consumido", "procesado")
_TIPOS_ALERTA_PERFIL = (
    "titulo_cambiado",
    "nueva_maestria",
    "nueva_especializacion",
    "cambio_correo_perfil",
    "nueva_institucion",
    "cambio_profesion",
)
_ESTADOS_ALERTA_PERFIL = ("pendiente", "enviada", "descartada")
_NIVELES_CRITICIDAD = ("critico", "alto", "medio", "bajo")
# "nivel_criticidad_enum" ya existe en la base de datos (creado por la
# Migracion 0005) -- `.create(checkfirst=True)` mas abajo es un no-op
# (detecta que ya existe); se recrea el objeto Python (mismos valores,
# mismo nombre) solo para poder referenciarlo como tipo de columna aqui,
# sin volver a intentar un CREATE TYPE real ni tocar su ciclo de vida
# (por eso NO se elimina en el downgrade de esta migracion).


def upgrade() -> None:
    estado_pm_enum = postgresql.ENUM(*_ESTADOS_PERSONA_MASTER, name="estado_persona_master_enum", create_type=False)
    estado_pm_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "personas_master",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.Uuid(), nullable=False, unique=True),
        sa.Column("persona_id", sa.Integer(), sa.ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("nombres", sa.String(200), nullable=False),
        sa.Column("apellidos", sa.String(200), nullable=False),
        sa.Column("fingerprint_principal", sa.String(500), nullable=True),
        sa.Column("fingerprint_fonetico", sa.String(500), nullable=True),
        sa.Column("sexo", sa.String(20), nullable=True),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column("correo_principal", sa.String(320), nullable=True),
        sa.Column("telefono_principal", sa.String(20), nullable=True),
        sa.Column("estado", estado_pm_enum, nullable=False, server_default="activa"),
        sa.Column("nivel_confianza", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("cantidad_fuentes", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("cantidad_cargos_historicos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fusionada_en_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="SET NULL"), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_persona_master_fingerprint", "personas_master", ["fingerprint_principal"])
    op.create_index("ix_persona_master_fingerprint_fonetico", "personas_master", ["fingerprint_fonetico"])
    op.create_index("ix_persona_master_correo", "personas_master", ["correo_principal"])
    op.create_index("ix_persona_master_estado", "personas_master", ["estado"])

    fuente_externa_enum = postgresql.ENUM(*_FUENTES_EXTERNAS, name="fuente_externa_enum", create_type=False)
    fuente_externa_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "registros_fuente",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fuente", fuente_externa_enum, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("datos", sa.JSON(), nullable=False),
        sa.Column("consultado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vigente", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hash_contenido", sa.String(64), nullable=True),
    )
    op.create_index("ix_registro_fuente_persona_master", "registros_fuente", ["persona_master_id"])
    op.create_index("ix_registro_fuente_vigente", "registros_fuente", ["persona_master_id", "fuente", "vigente"])

    op.create_table(
        "atributos_trazables",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campo", sa.String(100), nullable=False),
        sa.Column("valor", sa.Text(), nullable=False),
        sa.Column("fuente", fuente_externa_enum, nullable=False),
        sa.Column("obtenido_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("registro_fuente_id", sa.Integer(), sa.ForeignKey("registros_fuente.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_atributo_trazable_persona_master", "atributos_trazables", ["persona_master_id"])

    estado_revision_enum = postgresql.ENUM(*_ESTADOS_REVISION_IDENTIDAD, name="estado_revision_identidad_enum", create_type=False)
    estado_revision_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "casos_revision_identidad",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("persona_master_id_a", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("persona_master_id_b", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=True),
        sa.Column("registro_fuente_id", sa.Integer(), sa.ForeignKey("registros_fuente.id", ondelete="SET NULL"), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("explicacion", sa.Text(), nullable=False),
        sa.Column("campos_utilizados", sa.JSON(), nullable=False),
        sa.Column("estado", estado_revision_enum, nullable=False, server_default="pendiente_revision"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resuelto_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resuelto_por", sa.String(200), nullable=True),
        sa.Column("criterio_resolucion", sa.String(200), nullable=True),
    )
    op.create_index("ix_caso_revision_estado", "casos_revision_identidad", ["estado"])

    op.create_table(
        "consultas_fuente_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fuente", fuente_externa_enum, nullable=False),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exito", sa.Boolean(), nullable=True),
        sa.Column("duracion_segundos", sa.Float(), nullable=True),
        sa.Column("reintentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_consulta_fuente_persona_master", "consultas_fuente_log", ["persona_master_id", "fuente", "iniciado_en"]
    )

    tipo_evento_identidad_enum = postgresql.ENUM(*_TIPOS_EVENTO_IDENTIDAD, name="tipo_evento_identidad_enum", create_type=False)
    tipo_evento_identidad_enum.create(op.get_bind(), checkfirst=True)
    estado_evento_perfil_enum = postgresql.ENUM(*_ESTADOS_EVENTO_PERFIL, name="estado_evento_perfil_enum", create_type=False)
    estado_evento_perfil_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "eventos_perfil",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tipo", tipo_evento_identidad_enum, nullable=False),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("estado", estado_evento_perfil_enum, nullable=False, server_default="pendiente"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumido_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("procesado_en", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_evento_perfil_estado", "eventos_perfil", ["estado"])
    op.create_index("ix_evento_perfil_persona_master", "eventos_perfil", ["persona_master_id"])

    tipo_alerta_perfil_enum = postgresql.ENUM(*_TIPOS_ALERTA_PERFIL, name="tipo_alerta_perfil_enum", create_type=False)
    tipo_alerta_perfil_enum.create(op.get_bind(), checkfirst=True)
    estado_alerta_perfil_enum = postgresql.ENUM(*_ESTADOS_ALERTA_PERFIL, name="estado_alerta_perfil_enum", create_type=False)
    estado_alerta_perfil_enum.create(op.get_bind(), checkfirst=True)
    nivel_criticidad_enum = postgresql.ENUM(*_NIVELES_CRITICIDAD, name="nivel_criticidad_enum", create_type=False)
    nivel_criticidad_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "alertas_perfil",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("persona_master_id", sa.Integer(), sa.ForeignKey("personas_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", tipo_alerta_perfil_enum, nullable=False),
        sa.Column("prioridad", nivel_criticidad_enum, nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("detectado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", estado_alerta_perfil_enum, nullable=False, server_default="pendiente"),
        sa.Column("registro_fuente_id", sa.Integer(), sa.ForeignKey("registros_fuente.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_alerta_perfil_persona_master", "alertas_perfil", ["persona_master_id"])


def downgrade() -> None:
    op.drop_table("alertas_perfil")
    sa.Enum(name="estado_alerta_perfil_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_alerta_perfil_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("eventos_perfil")
    sa.Enum(name="estado_evento_perfil_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_evento_identidad_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("consultas_fuente_log")

    op.drop_table("casos_revision_identidad")
    sa.Enum(name="estado_revision_identidad_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("atributos_trazables")
    op.drop_table("registros_fuente")
    sa.Enum(name="fuente_externa_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("personas_master")
    sa.Enum(name="estado_persona_master_enum").drop(op.get_bind(), checkfirst=True)
