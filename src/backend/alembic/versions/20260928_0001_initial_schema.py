"""Create initial SCALD schema.

Revision ID: 20260928_0001
Revises:
Create Date: 2026-09-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260928_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("nombre", name="uq_roles_nombre"),
    )
    op.create_index("ix_roles_id", "roles", ["id"])
    op.create_index("ix_roles_nombre", "roles", ["nombre"])

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("apellido", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("rol_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
    )
    op.create_index("ix_usuarios_id", "usuarios", ["id"])
    op.create_index("ix_usuarios_email", "usuarios", ["email"])

    op.create_table(
        "hojas_ruta",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("ruta", sa.String(length=200), nullable=False),
        sa.Column("transporte", sa.String(length=200), nullable=True),
        sa.Column("cantidad_declarada", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="ACTIVA"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.Date(), nullable=False),
        sa.Column("updated_at", sa.Date(), nullable=False),
        sa.UniqueConstraint("codigo", name="uq_hojas_ruta_codigo"),
        sa.CheckConstraint("tipo IN ('HRD', 'HRE')", name="ck_hojas_ruta_tipo"),
        sa.CheckConstraint("cantidad_declarada >= 0", name="ck_hojas_ruta_cantidad"),
        sa.CheckConstraint("estado IN ('ACTIVA', 'INACTIVA', 'CERRADA')", name="ck_hojas_ruta_estado"),
    )
    op.create_index("ix_hojas_ruta_id", "hojas_ruta", ["id"])
    op.create_index("ix_hojas_ruta_codigo", "hojas_ruta", ["codigo"])

    op.create_table(
        "bultos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=100), nullable=False),
        sa.Column("hoja_ruta_id", sa.Integer(), sa.ForeignKey("hojas_ruta.id"), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False, server_default="PENDIENTE"),
        sa.Column("pistoleado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("info_adicional", sa.String(length=500), nullable=True),
        sa.UniqueConstraint("hoja_ruta_id", "codigo", name="uq_bultos_hoja_codigo"),
        sa.CheckConstraint("estado IN ('PENDIENTE', 'OK', 'FALTANTE', 'DUPLICADO', 'SIN LISTA', 'SIN HOJA', 'REASIGNADO')", name="ck_bultos_estado"),
    )
    op.create_index("ix_bultos_id", "bultos", ["id"])
    op.create_index("ix_bultos_codigo", "bultos", ["codigo"])

    op.create_table(
        "pistoleos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo_bulto", sa.String(length=100), nullable=False),
        sa.Column("hoja_ruta_id", sa.Integer(), sa.ForeignKey("hojas_ruta.id"), nullable=True),
        sa.Column("bulto_id", sa.Integer(), sa.ForeignKey("bultos.id"), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False, server_default="OK"),
        sa.Column("observacion", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_pistoleos_id", "pistoleos", ["id"])
    op.create_index("ix_pistoleos_codigo_bulto", "pistoleos", ["codigo_bulto"])

    op.create_table(
        "incidencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.String(length=60), nullable=False),
        sa.Column("hoja_ruta_id", sa.Integer(), sa.ForeignKey("hojas_ruta.id"), nullable=True),
        sa.Column("bulto_id", sa.Integer(), sa.ForeignKey("bultos.id"), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="PENDIENTE"),
        sa.Column("observaciones", sa.String(length=500), nullable=True),
        sa.Column("nueva_hoja_ruta_id", sa.Integer(), sa.ForeignKey("hojas_ruta.id"), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_resolucion", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("estado IN ('PENDIENTE', 'REGULARIZADO', 'REASIGNADO', 'ANULADO')", name="ck_incidencias_estado"),
    )
    op.create_index("ix_incidencias_id", "incidencias", ["id"])

    op.execute("INSERT INTO roles (nombre, descripcion) VALUES ('ADMIN', 'Administrador del sistema'), ('AUDITOR', 'Auditor logístico')")


def downgrade() -> None:
    op.drop_table("incidencias")
    op.drop_table("pistoleos")
    op.drop_table("bultos")
    op.drop_table("hojas_ruta")
    op.drop_table("usuarios")
    op.drop_table("roles")
