"""Respaldo manual de la base de datos (SQLite o PostgreSQL, según
DATABASE_URL) -- mismo comando para los dos motores, para no tener que
acordarse de cuál usar según el entorno.

No se ejecuta solo/automático -- cada respaldo es una acción explícita de
quien administra el sistema (por ejemplo, antes de cargar datos nuevos o
como rutina periódica manual). En Windows, para automatizarlo sin depender
de que alguien se acuerde, se puede programar con el Programador de tareas
(`schtasks`) apuntando a este mismo comando.

Uso: python backup_db.py
"""
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent
BACKUPS_DIR = BASE_DIR / "backups"

# Cuántos días de respaldos se conservan antes de purgar los más viejos --
# sin esto, backups/ crece sin límite para siempre. 30 días alcanza para
# cualquier "ay, esto se rompió la semana pasada" razonable; si se necesita
# retención más larga por política institucional, se ajusta acá.
DIAS_RETENCION = 30


def _respaldar_sqlite() -> Path | None:
    ruta_db = settings.database_url.split("///")[-1]
    origen = Path(ruta_db)
    if not origen.is_absolute():
        origen = BASE_DIR / origen
    if not origen.exists():
        print(f"No se encontró la base de datos en: {origen}")
        return None

    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = BACKUPS_DIR / f"{origen.stem}_{marca}.db"
    shutil.copy2(origen, destino)
    return destino


def _respaldar_postgres() -> Path | None:
    # postgresql+psycopg2://usuario:clave@host:5432/basededatos?sslmode=require
    # pg_dump no entiende el "+psycopg2" del dialecto de SQLAlchemy, así que
    # se arma la URL "pg://..." limpia a partir de las mismas piezas.
    partes = urlparse(settings.database_url.replace("+psycopg2", ""))
    if not partes.hostname or not partes.path.lstrip("/"):
        print("DATABASE_URL de Postgres incompleta -- falta host o nombre de base.")
        return None

    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_bd = partes.path.lstrip("/")
    destino = BACKUPS_DIR / f"{nombre_bd}_{marca}.dump"

    # -Fc (formato "custom", comprimido) en vez de un .sql plano: mismo
    # respaldo pesa una fracción y, a diferencia de un volcado de texto,
    # permite restaurar una sola tabla con pg_restore en vez de todo el
    # archivo si algún día solo se necesita recuperar un pedazo.
    comando = [
        "pg_dump",
        "-Fc",
        "-h", partes.hostname,
        "-p", str(partes.port or 5432),
        "-U", partes.username or "postgres",
        "-d", nombre_bd,
        "-f", str(destino),
    ]
    # La contraseña va por variable de entorno (PGPASSWORD), nunca en el
    # comando -- un argumento de proceso queda visible para cualquier otro
    # usuario del mismo equipo que corra `ps`/Task Manager mientras dura.
    entorno = {**os.environ, "PGPASSWORD": partes.password or ""}
    try:
        subprocess.run(comando, env=entorno, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("No se encontró `pg_dump` en el PATH -- instala el cliente de PostgreSQL (el mismo paquete que trae psql).")
        return None
    except subprocess.CalledProcessError as e:
        print(f"pg_dump falló:\n{e.stderr}")
        destino.unlink(missing_ok=True)
        return None
    return destino


def _purgar_antiguos() -> None:
    limite = datetime.now() - timedelta(days=DIAS_RETENCION)
    for archivo in BACKUPS_DIR.glob("*"):
        if archivo.is_file() and datetime.fromtimestamp(archivo.stat().st_mtime) < limite:
            archivo.unlink()
            print(f"Respaldo antiguo purgado (>{DIAS_RETENCION} días): {archivo.name}")


def respaldar() -> Path | None:
    BACKUPS_DIR.mkdir(exist_ok=True)
    es_postgres = settings.database_url.startswith("postgresql")
    destino = _respaldar_postgres() if es_postgres else _respaldar_sqlite()
    if destino:
        print(f"Respaldo creado: {destino}")
        _purgar_antiguos()
    return destino


if __name__ == "__main__":
    sys.exit(0 if respaldar() else 1)
