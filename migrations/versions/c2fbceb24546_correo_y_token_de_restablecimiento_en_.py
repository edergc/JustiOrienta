"""correo y token de restablecimiento en usuarios

Revision ID: c2fbceb24546
Revises: 1b6eb31d057c
Create Date: 2026-08-26 16:50:06.918877

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2fbceb24546'
down_revision: Union[str, Sequence[str], None] = '1b6eb31d057c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Nota: alembic --autogenerate también detectó dos foreign keys nuevas en
    consulta_log (sede_contexto_id, dependencia_resultado_id) -- columnas ya
    existentes de una migración anterior, nunca se les puso constraint real
    a propósito (ver esa migración). Fuera de alcance de este cambio, así
    que se quitaron de aquí igual que en las migraciones previas.
    """
    op.add_column('usuarios', sa.Column('email', sa.String(length=200), nullable=True))
    op.add_column('usuarios', sa.Column('reset_token_hash', sa.String(length=64), nullable=True))
    op.add_column('usuarios', sa.Column('reset_token_expira', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_usuarios_reset_token_hash'), 'usuarios', ['reset_token_hash'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_usuarios_reset_token_hash'), table_name='usuarios')
    op.drop_column('usuarios', 'reset_token_expira')
    op.drop_column('usuarios', 'reset_token_hash')
    op.drop_column('usuarios', 'email')
