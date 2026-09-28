"""Add transactional bulto reassignment history.

Revision ID: 20260928_0002
Revises: 20260928_0001
Create Date: 2026-09-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260928_0002"
down_revision: Union[str, None] = "20260928_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reasignaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bulto_id", sa.Integer(), sa.ForeignKey("bultos.id"), nullable=False),
        sa.Column("hoja_origen_id", sa.Integer(), sa.ForeignKey("hojas_ruta.id"), nullable=False),
        sa.Column("hoja_destino_id", sa.Integer(), sa.ForeignKey("hojas_ruta.id"), nullable=False),
        sa.Column("incidencia_id", sa.Integer(), sa.ForeignKey("incidencias.id"), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("motivo", sa.String(length=200), nullable=False),
        sa.Column("observaciones", sa.String(length=500), nullable=True),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="COMPLETADA"),
        sa.CheckConstraint("hoja_origen_id <> hoja_destino_id", name="ck_reasignaciones_hojas_distintas"),
        sa.CheckConstraint("estado IN ('COMPLETADA', 'ANULADA')", name="ck_reasignaciones_estado"),
    )
    op.create_index("ix_reasignaciones_id", "reasignaciones", ["id"])


def downgrade() -> None:
    op.drop_table("reasignaciones")
