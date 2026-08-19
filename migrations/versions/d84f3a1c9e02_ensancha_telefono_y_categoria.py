"""ensancha telefono y categoria (datos reales mas largos que el limite)

Revision ID: d84f3a1c9e02
Revises: c47a92f1e3b8
Create Date: 2026-08-19 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd84f3a1c9e02'
down_revision: Union[str, Sequence[str], None] = 'c47a92f1e3b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Estos límites alcanzaban en SQLite porque ahí el largo declarado en
    VARCHAR(n) es solo orientativo (SQLite nunca lo hace cumplir) -- pero
    migrando a PostgreSQL (que sí lo exige) la carga real del directorio
    oficial falló dos veces: hay teléfonos reales de hasta 80 caracteres
    ("Central: ... Operadora: Anexos ... - ...") y categorías de juzgado de
    hasta 124 ("Juzgado de Investigación Preparatoria Supraprovincial en
    Delitos Aduaneros, Tributarios, Propiedad Intelectual y Ambientales").
    Se deja margen holgado en vez de ajustar al límite exacto encontrado hoy.
    """
    with op.batch_alter_table('sedes', schema=None) as batch_op:
        batch_op.alter_column('telefono', existing_type=sa.String(length=40), type_=sa.String(length=150))
    with op.batch_alter_table('dependencias', schema=None) as batch_op:
        batch_op.alter_column('telefono', existing_type=sa.String(length=40), type_=sa.String(length=150))
        batch_op.alter_column('categoria', existing_type=sa.String(length=100), type_=sa.String(length=200))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('dependencias', schema=None) as batch_op:
        batch_op.alter_column('categoria', existing_type=sa.String(length=200), type_=sa.String(length=100))
        batch_op.alter_column('telefono', existing_type=sa.String(length=150), type_=sa.String(length=40))
    with op.batch_alter_table('sedes', schema=None) as batch_op:
        batch_op.alter_column('telefono', existing_type=sa.String(length=150), type_=sa.String(length=40))
