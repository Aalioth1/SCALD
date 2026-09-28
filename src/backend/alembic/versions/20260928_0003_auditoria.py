"""Add operation audit log.

Revision ID: 20260928_0003
Revises: 20260928_0002
Create Date: 2026-09-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260928_0003"
down_revision: Union[str, None] = "20260928_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("entidad", sa.String(length=80), nullable=False),
        sa.Column("entidad_id", sa.Integer(), nullable=True),
        sa.Column("accion", sa.String(length=40), nullable=False),
        sa.Column("datos_anteriores", sa.JSON(), nullable=True),
        sa.Column("datos_nuevos", sa.JSON(), nullable=True),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origen", sa.String(length=80), nullable=False, server_default="API"),
        sa.Column("correlation_id", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_auditoria_id", "auditoria", ["id"])
    op.create_index("ix_auditoria_entidad", "auditoria", ["entidad", "entidad_id"])
    op.create_index("ix_auditoria_fecha_hora", "auditoria", ["fecha_hora"])


def downgrade() -> None:
    op.drop_table("auditoria")
