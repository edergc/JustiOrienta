"""forzar cambio de contraseña en el primer login

Revision ID: c47a92f1e3b8
Revises: b21e6a9d4f10
Create Date: 2026-08-18 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c47a92f1e3b8'
down_revision: Union[str, Sequence[str], None] = 'b21e6a9d4f10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Cuentas ya existentes quedan en False (no se les fuerza el cambio
    retroactivamente): esto solo aplica hacia adelante, a cuentas nuevas o
    a las que un(a) admin restablezca la contraseña desde ahora.
    """
    op.add_column('usuarios', sa.Column('debe_cambiar_password', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_column('debe_cambiar_password')
