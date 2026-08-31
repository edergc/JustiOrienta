from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

es_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if es_sqlite else {}
# pool_pre_ping: Neon (Postgres serverless) suspende y corta conexiones
# inactivas por su cuenta, y Render free tier duerme el proceso completo --
# sin esto, la primera consulta tras un rato de inactividad fallaba con
# "SSL connection has been closed unexpectedly" en vez de reconectar sola.
# No aplica a SQLite (sin servidor, no hay conexión que se caiga).
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=not es_sqlite,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
