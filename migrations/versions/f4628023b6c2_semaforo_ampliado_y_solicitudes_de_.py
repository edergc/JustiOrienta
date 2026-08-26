"""semaforo ampliado y solicitudes de cobertura

Revision ID: f4628023b6c2
Revises: 4a21bfe5eaf9
Create Date: 2026-08-26 11:40:42.787937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4628023b6c2'
down_revision: Union[str, Sequence[str], None] = '4a21bfe5eaf9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Deliberadamente NO se agregan aqui las llaves foraneas de
    consulta_log que el autogenerate tambien detecto (sede_contexto_id,
    dependencia_resultado_id): son una correccion valida pero ajena al
    proposito de esta migracion (semaforo ampliado + solicitudes de
    cobertura) -- se dejan fuera para que este cambio en produccion sea
    minimo y predecible, no una mezcla de cosas distintas.
    """
    op.create_table('solicitudes_cobertura',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('query_text', sa.String(length=300), nullable=False),
    sa.Column('area', sa.String(length=150), nullable=True),
    sa.Column('estado', sa.String(length=20), nullable=True),
    sa.Column('comentario', sa.Text(), nullable=True),
    sa.Column('creado_por', sa.String(length=8), nullable=True),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_solicitudes_cobertura_area'), 'solicitudes_cobertura', ['area'], unique=False)
    op.create_index(op.f('ix_solicitudes_cobertura_estado'), 'solicitudes_cobertura', ['estado'], unique=False)
    op.create_index(op.f('ix_solicitudes_cobertura_id'), 'solicitudes_cobertura', ['id'], unique=False)
    op.add_column('dependencias', sa.Column('validado_por', sa.String(length=200), nullable=True))
    op.add_column('dependencias', sa.Column('proxima_revision', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('dependencias', 'proxima_revision')
    op.drop_column('dependencias', 'validado_por')
    op.drop_index(op.f('ix_solicitudes_cobertura_id'), table_name='solicitudes_cobertura')
    op.drop_index(op.f('ix_solicitudes_cobertura_estado'), table_name='solicitudes_cobertura')
    op.drop_index(op.f('ix_solicitudes_cobertura_area'), table_name='solicitudes_cobertura')
    op.drop_table('solicitudes_cobertura')
