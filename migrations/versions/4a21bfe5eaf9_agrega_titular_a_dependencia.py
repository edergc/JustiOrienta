"""agrega titular a dependencia

Revision ID: 4a21bfe5eaf9
Revises: d84f3a1c9e02
Create Date: 2026-08-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "4a21bfe5eaf9"
down_revision = "d84f3a1c9e02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("dependencias", sa.Column("titular", sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column("dependencias", "titular")
