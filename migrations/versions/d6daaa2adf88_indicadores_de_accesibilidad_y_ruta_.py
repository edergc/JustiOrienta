"""indicadores de accesibilidad y ruta interna

Revision ID: d6daaa2adf88
Revises: c1bae2d4ea7a
Create Date: 2026-08-17 15:57:52.595439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6daaa2adf88'
down_revision: Union[str, Sequence[str], None] = 'c1bae2d4ea7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Las llaves foráneas nuevas de consulta_log se dejan solo a nivel de ORM
    (sin op.create_foreign_key): SQLite no soporta ALTER TABLE ADD CONSTRAINT
    y forzarlo con batch mode implicaría reconstruir toda la tabla -- para un
    registro de analítica anónima y de solo lectura no vale la pena el
    riesgo. En PostgreSQL (producción) sí se podrían agregar sin problema.
    """
    op.add_column('consulta_log', sa.Column('sede_contexto_id', sa.Integer(), nullable=True))
    op.add_column('consulta_log', sa.Column('dependencia_resultado_id', sa.Integer(), nullable=True))
    op.add_column('consulta_log', sa.Column('modo_accesible', sa.Boolean(), nullable=True))
    op.add_column('consulta_log', sa.Column('via_voz', sa.Boolean(), nullable=True))
    op.add_column('consulta_log', sa.Column('sobre_accesibilidad', sa.Boolean(), nullable=True))
    op.add_column('dependencias', sa.Column('instrucciones_internas', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('dependencias', 'instrucciones_internas')
    op.drop_column('consulta_log', 'sobre_accesibilidad')
    op.drop_column('consulta_log', 'via_voz')
    op.drop_column('consulta_log', 'modo_accesible')
    op.drop_column('consulta_log', 'dependencia_resultado_id')
    op.drop_column('consulta_log', 'sede_contexto_id')
