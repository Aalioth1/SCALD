"""Marca si un usuario puede iniciar sesión.

Revision ID: 20261001_0005
Revises: 20261001_0004
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261001_0005"
down_revision: Union[str, None] = "20261001_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "activo")
