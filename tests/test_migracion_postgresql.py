"""No corre contra PostgreSQL de verdad (la suite usa SQLite en memoria) --
eso se verificó manualmente contra una instancia real (ver README, sección
"Producción vs. desarrollo"). Esto solo deja una guardia de regresión: si
alguien vuelve a angostar estas columnas sin darse cuenta, SQLite no se
quejaría (ahí el largo declarado es solo orientativo), pero Postgres sí --
exactamente el bug que motivó ensancharlas."""
from app import models


def test_telefono_tiene_margen_para_datos_reales():
    # El directorio oficial real trae teléfonos de hasta 80 caracteres
    # ("Central: ... Operadora: Anexos ... - ...").
    assert models.Sede.__table__.columns["telefono"].type.length >= 150
    assert models.Dependencia.__table__.columns["telefono"].type.length >= 150


def test_categoria_tiene_margen_para_datos_reales():
    # El directorio oficial real trae categorías de hasta 124 caracteres
    # (especialidades de juzgado largas).
    assert models.Dependencia.__table__.columns["categoria"].type.length >= 200
