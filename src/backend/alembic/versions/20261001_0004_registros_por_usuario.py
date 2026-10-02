"""Asocia hojas de ruta y bultos al usuario que los cargó.

Revision ID: 20261001_0004
Revises: 20260928_0003
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261001_0004"
down_revision: Union[str, None] = "20260928_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("hojas_ruta", sa.Column("usuario_id", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE hojas_ruta
            SET usuario_id = (SELECT id FROM usuarios ORDER BY id LIMIT 1)
            WHERE usuario_id IS NULL
            """
        )
    )
    bind = op.get_bind()
    hojas_sin_usuario = bind.execute(sa.text("SELECT COUNT(*) FROM hojas_ruta WHERE usuario_id IS NULL")).scalar()
    if hojas_sin_usuario:
        raise RuntimeError("Hay hojas de ruta existentes y ningún usuario para asignarlas.")

    op.alter_column("hojas_ruta", "usuario_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_hojas_ruta_usuario_id_usuarios", "hojas_ruta", "usuarios", ["usuario_id"], ["id"])
    op.create_index("ix_hojas_ruta_usuario_id", "hojas_ruta", ["usuario_id"])
    op.drop_constraint("uq_hojas_ruta_codigo", "hojas_ruta", type_="unique")
    op.create_unique_constraint("uq_hojas_ruta_usuario_codigo", "hojas_ruta", ["usuario_id", "codigo"])

    op.add_column("bultos", sa.Column("usuario_id", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE bultos
            SET usuario_id = (
                SELECT hojas_ruta.usuario_id
                FROM hojas_ruta
                WHERE hojas_ruta.id = bultos.hoja_ruta_id
            )
            WHERE usuario_id IS NULL
            """
        )
    )
    bultos_sin_usuario = bind.execute(sa.text("SELECT COUNT(*) FROM bultos WHERE usuario_id IS NULL")).scalar()
    if bultos_sin_usuario:
        raise RuntimeError("Hay bultos existentes cuya hoja de ruta no tiene usuario.")

    op.alter_column("bultos", "usuario_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_bultos_usuario_id_usuarios", "bultos", "usuarios", ["usuario_id"], ["id"])
    op.create_index("ix_bultos_usuario_id", "bultos", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_bultos_usuario_id", table_name="bultos")
    op.drop_constraint("fk_bultos_usuario_id_usuarios", "bultos", type_="foreignkey")
    op.drop_column("bultos", "usuario_id")

    op.drop_constraint("uq_hojas_ruta_usuario_codigo", "hojas_ruta", type_="unique")
    op.create_unique_constraint("uq_hojas_ruta_codigo", "hojas_ruta", ["codigo"])
    op.drop_index("ix_hojas_ruta_usuario_id", table_name="hojas_ruta")
    op.drop_constraint("fk_hojas_ruta_usuario_id_usuarios", "hojas_ruta", type_="foreignkey")
    op.drop_column("hojas_ruta", "usuario_id")
