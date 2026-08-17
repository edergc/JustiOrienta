"""login por dni en vez de correo

Revision ID: e88bf8bbbc11
Revises: d6daaa2adf88
Create Date: 2026-08-17 16:36:09.616768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e88bf8bbbc11'
down_revision: Union[str, Sequence[str], None] = 'd6daaa2adf88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Las llaves foráneas nuevas de consulta_log NO se agregan aquí a propósito
    (mismo motivo que la migración anterior: SQLite no soporta ALTER TABLE ADD
    CONSTRAINT sin reconstruir la tabla completa, y para un registro de
    analítica de solo lectura no vale la pena el riesgo).
    """
    # auditoria.usuario_email -> auditoria.usuario_dni: se conserva el valor
    # tal cual, son solo registros históricos de auditoría, no credenciales.
    op.add_column('auditoria', sa.Column('usuario_dni', sa.String(length=8), nullable=True))
    op.execute('UPDATE auditoria SET usuario_dni = usuario_email')
    with op.batch_alter_table('auditoria', schema=None) as batch_op:
        batch_op.drop_column('usuario_email')

    # usuarios.email -> usuarios.dni: el acceso pasa a ser por DNI (8 dígitos),
    # el dato que toda persona en Perú tiene con certeza, en vez de un correo
    # institucional que no todas las áreas tienen asignado.
    op.add_column('usuarios', sa.Column('dni', sa.String(length=8), nullable=True))
    op.execute("UPDATE usuarios SET dni = '12345678' WHERE email = 'admin@justiciaorienta.local'")
    # Cualquier otra cuenta (de prueba) que no sea la admin conocida recibe un
    # DNI de relleno único -- nunca uno real, este piloto no tenía esos datos
    # -- solo para poder aplicar la restricción NOT NULL + UNIQUE que sigue.
    op.execute("UPDATE usuarios SET dni = printf('%08d', id) WHERE dni IS NULL")
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_index('ix_usuarios_email')
        batch_op.drop_column('email')
        batch_op.alter_column('dni', existing_type=sa.String(length=8), nullable=False)
        batch_op.create_index(batch_op.f('ix_usuarios_dni'), ['dni'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_usuarios_dni'))
        batch_op.add_column(sa.Column('email', sa.String(length=150), nullable=False, server_default=''))
        batch_op.create_index('ix_usuarios_email', ['email'], unique=True)
        batch_op.drop_column('dni')

    with op.batch_alter_table('auditoria', schema=None) as batch_op:
        batch_op.add_column(sa.Column('usuario_email', sa.String(length=150), nullable=True))
    op.execute('UPDATE auditoria SET usuario_email = usuario_dni')
    with op.batch_alter_table('auditoria', schema=None) as batch_op:
        batch_op.drop_column('usuario_dni')
