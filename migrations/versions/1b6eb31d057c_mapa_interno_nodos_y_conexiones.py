"""mapa interno: nodos y conexiones

Revision ID: 1b6eb31d057c
Revises: f4628023b6c2
Create Date: 2026-08-26 12:55:45.279420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b6eb31d057c'
down_revision: Union[str, Sequence[str], None] = 'f4628023b6c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Deliberadamente NO se agregan aqui las llaves foraneas de consulta_log
    que el autogenerate tambien detecto (sede_contexto_id,
    dependencia_resultado_id) -- correccion valida pero ajena al proposito
    de esta migracion, igual que en f4628023b6c2.
    """
    op.create_table('nodos_ubicacion',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sede_id', sa.Integer(), nullable=False),
    sa.Column('piso', sa.String(length=30), nullable=True),
    sa.Column('nombre', sa.String(length=200), nullable=False),
    sa.Column('es_punto_partida', sa.Boolean(), nullable=True),
    sa.Column('dependencia_id', sa.Integer(), nullable=True),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['dependencia_id'], ['dependencias.id'], ),
    sa.ForeignKeyConstraint(['sede_id'], ['sedes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nodos_ubicacion_dependencia_id'), 'nodos_ubicacion', ['dependencia_id'], unique=False)
    op.create_index(op.f('ix_nodos_ubicacion_id'), 'nodos_ubicacion', ['id'], unique=False)
    op.create_index(op.f('ix_nodos_ubicacion_sede_id'), 'nodos_ubicacion', ['sede_id'], unique=False)
    op.create_table('conexiones_nodo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nodo_a_id', sa.Integer(), nullable=False),
    sa.Column('nodo_b_id', sa.Integer(), nullable=False),
    sa.Column('distancia', sa.Integer(), nullable=True),
    sa.Column('instruccion_a_b', sa.Text(), nullable=True),
    sa.Column('instruccion_b_a', sa.Text(), nullable=True),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['nodo_a_id'], ['nodos_ubicacion.id'], ),
    sa.ForeignKeyConstraint(['nodo_b_id'], ['nodos_ubicacion.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conexiones_nodo_id'), 'conexiones_nodo', ['id'], unique=False)
    op.create_index(op.f('ix_conexiones_nodo_nodo_a_id'), 'conexiones_nodo', ['nodo_a_id'], unique=False)
    op.create_index(op.f('ix_conexiones_nodo_nodo_b_id'), 'conexiones_nodo', ['nodo_b_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_conexiones_nodo_nodo_b_id'), table_name='conexiones_nodo')
    op.drop_index(op.f('ix_conexiones_nodo_nodo_a_id'), table_name='conexiones_nodo')
    op.drop_index(op.f('ix_conexiones_nodo_id'), table_name='conexiones_nodo')
    op.drop_table('conexiones_nodo')
    op.drop_index(op.f('ix_nodos_ubicacion_sede_id'), table_name='nodos_ubicacion')
    op.drop_index(op.f('ix_nodos_ubicacion_id'), table_name='nodos_ubicacion')
    op.drop_index(op.f('ix_nodos_ubicacion_dependencia_id'), table_name='nodos_ubicacion')
    op.drop_table('nodos_ubicacion')
