"""ruta accesible en conexiones del mapa interno

Revision ID: 5b559732eeff
Revises: 7f24a68f85d8
Create Date: 2026-08-28 11:46:32.410179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b559732eeff'
down_revision: Union[str, Sequence[str], None] = '7f24a68f85d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Deliberadamente NO se agregan aqui las llaves foraneas de consulta_log
    que el autogenerate tambien detecto (dependencia_resultado_id,
    sede_contexto_id): mismo criterio que la migracion anterior
    (f4628023b6c2) -- son una correccion valida pero ajena al proposito de
    esta migracion, se dejan fuera para que el cambio en produccion sea
    minimo y predecible.

    server_default=true (no solo el default=True del modelo en Python): la
    tabla conexiones_nodo ya tiene filas reales cargadas (la sede piloto), y
    un ALTER TABLE ... NOT NULL sin default de servidor falla contra esas
    filas existentes.
    """
    op.add_column(
        'conexiones_nodo',
        sa.Column('es_accesible', sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('conexiones_nodo', 'es_accesible')
