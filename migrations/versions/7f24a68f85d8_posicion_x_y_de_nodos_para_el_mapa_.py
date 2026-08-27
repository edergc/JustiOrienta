"""posicion x y de nodos para el mapa visual

Revision ID: 7f24a68f85d8
Revises: c2fbceb24546
Create Date: 2026-08-27 09:23:36.081870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f24a68f85d8'
down_revision: Union[str, Sequence[str], None] = 'c2fbceb24546'
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
    op.add_column('nodos_ubicacion', sa.Column('pos_x', sa.Float(), nullable=True))
    op.add_column('nodos_ubicacion', sa.Column('pos_y', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('nodos_ubicacion', 'pos_y')
    op.drop_column('nodos_ubicacion', 'pos_x')
