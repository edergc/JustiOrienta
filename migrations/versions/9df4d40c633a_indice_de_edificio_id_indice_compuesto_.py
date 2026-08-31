"""indice de edificio_id, indice compuesto de auditoria y fk real de consulta_log

Revision ID: 9df4d40c633a
Revises: 5e91586b42a9
Create Date: 2026-08-31 16:29:11.920513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9df4d40c633a'
down_revision: Union[str, Sequence[str], None] = '5e91586b42a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Tres ajustes menores de estructura encontrados en una revisión general
    de la base, ninguno corrige un error visible hoy (a diferencia de
    5e91586b42a9), pero los tres importan de cara a Postgres real:

    1. dependencias.edificio_id era la única llave foránea del esquema sin
       índice -- inconsistente con el resto y usada en joins.
    2. auditoria tenía dos índices de una sola columna (entidad, entidad_id)
       cuando la única consulta real (listar_por_entidad) siempre filtra
       ambas juntas -- un índice compuesto sirve esa consulta igual de bien
       con menos costo de escritura en cada inserción de auditoría.
    3. consulta_log.sede_contexto_id y dependencia_resultado_id nunca
       tuvieron el FOREIGN KEY real en la base (ver d6daaa2adf88 y
       e88bf8bbbc11): se dejaron solo a nivel de ORM por una limitación de
       SQLite, pero esa migración nunca se completó del lado de Postgres,
       que sí lo soporta sin problema. NOT VALID: agrega la restricción sin
       escanear ni bloquear las filas existentes -- válida de inmediato
       para todo lo que se inserte de ahora en adelante; si se quiere que
       también cubra el historial ya cargado, se corre por separado
       "ALTER TABLE consulta_log VALIDATE CONSTRAINT ..." cuando convenga.
    """
    op.create_index(op.f("ix_dependencias_edificio_id"), "dependencias", ["edificio_id"], unique=False)

    op.create_index("ix_auditoria_entidad_entidad_id", "auditoria", ["entidad", "entidad_id"], unique=False)
    op.drop_index(op.f("ix_auditoria_entidad"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_entidad_id"), table_name="auditoria")

    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE consulta_log ADD CONSTRAINT fk_consulta_log_sede_contexto_id "
            "FOREIGN KEY (sede_contexto_id) REFERENCES sedes (id) NOT VALID"
        )
        op.execute(
            "ALTER TABLE consulta_log ADD CONSTRAINT fk_consulta_log_dependencia_resultado_id "
            "FOREIGN KEY (dependencia_resultado_id) REFERENCES dependencias (id) NOT VALID"
        )


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE consulta_log DROP CONSTRAINT fk_consulta_log_dependencia_resultado_id")
        op.execute("ALTER TABLE consulta_log DROP CONSTRAINT fk_consulta_log_sede_contexto_id")

    op.create_index(op.f("ix_auditoria_entidad_id"), "auditoria", ["entidad_id"], unique=False)
    op.create_index(op.f("ix_auditoria_entidad"), "auditoria", ["entidad"], unique=False)
    op.drop_index("ix_auditoria_entidad_entidad_id", table_name="auditoria")

    op.drop_index(op.f("ix_dependencias_edificio_id"), table_name="dependencias")
