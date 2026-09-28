"""Añade vocabulario explícito para validación individual de abogados."""

from __future__ import annotations

from alembic import op

revision = "0010_validacion_abogado_enums"
down_revision = "0009_orquestador"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL no permite ALTER TYPE ... ADD VALUE dentro de una transacción usada después.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE fuente_externa_enum ADD VALUE IF NOT EXISTS 'consultas_ecuador'")
        op.execute("ALTER TYPE tipo_trabajo_orquestador_enum ADD VALUE IF NOT EXISTS 'validacion_abogado'")
        op.execute("ALTER TYPE tipo_paso_pipeline_enum ADD VALUE IF NOT EXISTS 'identificacion'")
        op.execute("ALTER TYPE tipo_paso_pipeline_enum ADD VALUE IF NOT EXISTS 'matching_identidad'")
        op.execute("ALTER TYPE tipo_paso_pipeline_enum ADD VALUE IF NOT EXISTS 'persistencia'")


def downgrade() -> None:
    # PostgreSQL no permite eliminar valores de ENUM sin recrear el tipo.
    pass
