"""solicitudes de atencion con codigo de seguimiento

Revision ID: 89d35f1b61b3
Revises: 5b559732eeff
Create Date: 2026-08-31 14:25:00.299919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89d35f1b61b3'
down_revision: Union[str, Sequence[str], None] = '5b559732eeff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Deliberadamente NO se agregan aqui las llaves foraneas de consulta_log
    que el autogenerate tambien detecto (dependencia_resultado_id,
    sede_contexto_id): mismo criterio que las migraciones anteriores
    (f4628023b6c2, 5b559732eeff) -- correccion valida pero ajena al
    proposito de esta migracion, se deja fuera para que el cambio en
    produccion sea minimo y predecible. Tabla nueva, sin filas existentes,
    asi que no hace falta ningun server_default.
    """
    op.create_table('solicitudes_atencion',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=20), nullable=False),
    sa.Column('nombre_contacto', sa.String(length=200), nullable=False),
    sa.Column('telefono', sa.String(length=50), nullable=True),
    sa.Column('correo', sa.String(length=200), nullable=True),
    sa.Column('motivo', sa.Text(), nullable=False),
    sa.Column('area', sa.String(length=150), nullable=True),
    sa.Column('estado', sa.String(length=20), nullable=True),
    sa.Column('comentario', sa.Text(), nullable=True),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_solicitudes_atencion_area'), 'solicitudes_atencion', ['area'], unique=False)
    op.create_index(op.f('ix_solicitudes_atencion_codigo'), 'solicitudes_atencion', ['codigo'], unique=True)
    op.create_index(op.f('ix_solicitudes_atencion_estado'), 'solicitudes_atencion', ['estado'], unique=False)
    op.create_index(op.f('ix_solicitudes_atencion_id'), 'solicitudes_atencion', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_solicitudes_atencion_id'), table_name='solicitudes_atencion')
    op.drop_index(op.f('ix_solicitudes_atencion_estado'), table_name='solicitudes_atencion')
    op.drop_index(op.f('ix_solicitudes_atencion_codigo'), table_name='solicitudes_atencion')
    op.drop_index(op.f('ix_solicitudes_atencion_area'), table_name='solicitudes_atencion')
    op.drop_table('solicitudes_atencion')
