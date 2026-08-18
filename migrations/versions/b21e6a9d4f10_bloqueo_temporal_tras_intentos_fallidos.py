"""bloqueo temporal de cuenta tras intentos fallidos de login

Revision ID: b21e6a9d4f10
Revises: 617da8f0a4dd
Create Date: 2026-08-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b21e6a9d4f10'
down_revision: Union[str, Sequence[str], None] = '617da8f0a4dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('usuarios', sa.Column('intentos_fallidos', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('usuarios', sa.Column('bloqueado_hasta', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_column('bloqueado_hasta')
        batch_op.drop_column('intentos_fallidos')
