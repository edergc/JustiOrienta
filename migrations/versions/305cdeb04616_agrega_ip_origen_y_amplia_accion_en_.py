"""agrega ip_origen y amplia accion en auditoria

Revision ID: 305cdeb04616
Revises: 9df4d40c633a
Create Date: 2026-09-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '305cdeb04616'
down_revision: Union[str, Sequence[str], None] = '9df4d40c633a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Profesionaliza la auditoria de cara al testeo de TI: hasta ahora solo
    registraba cambios de contenido del catalogo, nunca eventos de sesion
    (login, bloqueo de cuenta, cambio de password) ni exportaciones masivas
    -- lo primero que pide un auditor de seguridad. Dos cambios de esquema
    para soportar eso:

    1. ip_origen: contexto forense minimo (desde donde se hizo la accion).
       Nullable porque las filas ya existentes no lo tienen.
    2. accion pasa de String(20) a String(30): los nuevos nombres de evento
       de sesion (ej. "PASSWORD_RESTABLECIDA") no entraban en 20 caracteres.
    """
    op.add_column("auditoria", sa.Column("ip_origen", sa.String(45), nullable=True))
    op.alter_column("auditoria", "accion", type_=sa.String(30), existing_type=sa.String(20))


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("auditoria", "accion", type_=sa.String(20), existing_type=sa.String(30))
    op.drop_column("auditoria", "ip_origen")
