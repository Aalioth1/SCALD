"""Situación de la hoja: vigente para el auditor, archivada o eliminada en el historial.

Revision ID: 20261001_0006
Revises: 20261001_0005
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261001_0006"
down_revision: Union[str, None] = "20261001_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "hojas_ruta",
        sa.Column("situacion", sa.String(length=20), nullable=False, server_default="VIGENTE"),
    )
    op.create_check_constraint(
        "ck_hojas_ruta_situacion",
        "hojas_ruta",
        "situacion IN ('VIGENTE', 'ARCHIVADO', 'ELIMINADO')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_hojas_ruta_situacion", "hojas_ruta", type_="check")
    op.drop_column("hojas_ruta", "situacion")
