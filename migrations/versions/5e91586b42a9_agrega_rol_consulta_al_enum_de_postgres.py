"""agrega rol consulta al enum de postgres

Revision ID: 5e91586b42a9
Revises: 89d35f1b61b3
Create Date: 2026-08-31 16:18:07.215269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e91586b42a9'
down_revision: Union[str, Sequence[str], None] = '89d35f1b61b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    El modelo (app/models/usuario.py) define el rol "consulta" desde antes
    de esta migración, pero el tipo ENUM real de PostgreSQL se quedó con
    los 4 valores originales de la migración inicial (23756a617f37) -- nadie
    agregó el quinto ahí. En SQLite un Enum no es un tipo nativo, así que el
    error nunca aparecía en desarrollo ni en las pruebas; en Postgres, crear
    un usuario con rol="consulta" (posible desde el panel) fallaba con
    "invalid input value for enum rol". IF NOT EXISTS lo vuelve seguro de
    correr más de una vez.

    No aplica en SQLite (no tiene tipos ENUM nativos que alterar).
    """
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE rol ADD VALUE IF NOT EXISTS 'consulta'")


def downgrade() -> None:
    """Downgrade schema.

    PostgreSQL no soporta quitar un valor de un ENUM (no existe "ALTER TYPE
    ... DROP VALUE"). Revertir de verdad exigiría recrear el tipo entero y
    reasignar la columna -- riesgo innecesario para un downgrade; si algún
    día hace falta, se hace a mano.
    """
    pass
