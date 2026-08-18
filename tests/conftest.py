import os

os.environ["JUSTICIA_ORIENTA_SECRET"] = "clave-de-pruebas"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models, security
from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def base_de_datos_limpia():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sede(db):
    s = models.Sede(nombre="Sede de Pruebas")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@pytest.fixture
def admin_usuario(db):
    u = models.Usuario(
        nombre="Admin de Pruebas",
        dni="10000001",
        password_hash=security.hash_password("clave123"),
        rol=models.Rol.admin,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def gestor_usuario(db):
    u = models.Usuario(
        nombre="Gestor de Pruebas",
        dni="10000002",
        password_hash=security.hash_password("clave123"),
        rol=models.Rol.gestor,
        area="Recursos Humanos",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def validador_usuario(db):
    u = models.Usuario(
        nombre="Validador de Pruebas",
        dni="10000003",
        password_hash=security.hash_password("clave123"),
        rol=models.Rol.validador,
        area="Recursos Humanos",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def consulta_usuario(db):
    u = models.Usuario(
        nombre="Consulta de Pruebas",
        dni="10000004",
        password_hash=security.hash_password("clave123"),
        rol=models.Rol.consulta,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def token_para(dni: str) -> str:
    return security.crear_token(dni)
