"""indices en las llaves foraneas de consulta_log

Revision ID: 617da8f0a4dd
Revises: e88bf8bbbc11
Create Date: 2026-08-18 10:38:51.983493

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '617da8f0a4dd'
down_revision: Union[str, Sequence[str], None] = 'e88bf8bbbc11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Solo los índices -- las llaves foráneas se dejan a nivel de ORM nada más,
    mismo motivo que en migraciones anteriores de esta tabla: SQLite no
    soporta ALTER TABLE ADD CONSTRAINT sin reconstruir la tabla completa.
    """
    op.create_index(op.f('ix_consulta_log_dependencia_resultado_id'), 'consulta_log', ['dependencia_resultado_id'], unique=False)
    op.create_index(op.f('ix_consulta_log_sede_contexto_id'), 'consulta_log', ['sede_contexto_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_consulta_log_sede_contexto_id'), table_name='consulta_log')
    op.drop_index(op.f('ix_consulta_log_dependencia_resultado_id'), table_name='consulta_log')
