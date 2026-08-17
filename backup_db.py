"""Respaldo manual de la base de datos SQLite.

No se ejecuta solo/automático -- cada respaldo es una acción explícita de
quien administra el sistema (por ejemplo, antes de cargar datos nuevos o
como rutina periódica manual). En producción con PostgreSQL, este script se
reemplaza por `pg_dump` según la política de respaldos del área de TI.

Uso: python backup_db.py
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent
BACKUPS_DIR = BASE_DIR / "backups"


def respaldar() -> Path | None:
    if not settings.database_url.startswith("sqlite"):
        print("Este script respalda SQLite. En Postgres, usa pg_dump.")
        return None

    ruta_db = settings.database_url.split("///")[-1]
    origen = Path(ruta_db)
    if not origen.is_absolute():
        origen = BASE_DIR / origen
    if not origen.exists():
        print(f"No se encontró la base de datos en: {origen}")
        return None

    BACKUPS_DIR.mkdir(exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = BACKUPS_DIR / f"{origen.stem}_{marca}.db"
    shutil.copy2(origen, destino)
    print(f"Respaldo creado: {destino}")
    return destino


if __name__ == "__main__":
    sys.exit(0 if respaldar() else 1)
