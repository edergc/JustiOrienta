"""Conexión a base de datos.

Por defecto usa SQLite (cero instalación, ideal para desarrollo y para el piloto).
Para producción, basta con definir la variable de entorno DATABASE_URL apuntando
a PostgreSQL -- SQLAlchemy no requiere cambios de código:

    DATABASE_URL=postgresql+psycopg2://usuario:clave@host:5432/justicia_orienta

Tanto SQLite como PostgreSQL son software libre, sin costo de licenciamiento.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./justicia_orienta.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
