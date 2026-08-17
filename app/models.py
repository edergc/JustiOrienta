import re
import unicodedata
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, event,
)
from sqlalchemy.orm import relationship

from app.database import Base


def normalizar(texto: str) -> str:
    """minúsculas, sin tildes, sin signos, espacios simples -- usado para búsqueda."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    rol = Column(String(20), nullable=False, default="gestor")  # admin | gestor
    area = Column(String(150), nullable=True)  # área que puede editar, si rol=gestor
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)


class Dependencia(Base):
    __tablename__ = "dependencias"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(30), nullable=False)  # jurisdiccional | administrativa | servicio
    categoria = Column(String(100))
    nombre = Column(String(200), nullable=False)
    nombre_normalizado = Column(String(200), index=True)

    sede = Column(String(150))
    edificio = Column(String(150))
    piso = Column(String(30))
    oficina = Column(String(50))

    horario = Column(String(300))
    servicios = Column(Text)
    requisitos = Column(Text)
    telefono = Column(String(40))
    correo = Column(String(150))

    rampa = Column(Boolean, default=False)
    ascensor = Column(Boolean, default=False)
    banio_accesible = Column(Boolean, default=False)
    ruta_accesible = Column(Boolean, default=False)

    estado = Column(String(20), default="revision")  # activo | revision | inactivo
    area = Column(String(150))  # para restringir edición por gestor
    responsable_validar = Column(String(200))

    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    alias = relationship("Alias", back_populates="dependencia", cascade="all, delete-orphan")


class Alias(Base):
    __tablename__ = "alias"

    id = Column(Integer, primary_key=True, index=True)
    dependencia_id = Column(Integer, ForeignKey("dependencias.id"), nullable=False)
    alias = Column(String(200), nullable=False)
    alias_normalizado = Column(String(200), index=True)

    dependencia = relationship("Dependencia", back_populates="alias")


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_email = Column(String(150))
    dependencia_id = Column(Integer, nullable=True)
    accion = Column(String(20))  # CREATE | UPDATE | DELETE
    detalle = Column(Text)
    fecha = Column(DateTime, default=datetime.utcnow)


class ConsultaLog(Base):
    """Registro anónimo de uso -- sin datos personales, solo el texto de la consulta."""
    __tablename__ = "consulta_log"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(300))
    encontrado = Column(Boolean, default=False)
    fecha = Column(DateTime, default=datetime.utcnow)


@event.listens_for(Dependencia, "before_insert")
@event.listens_for(Dependencia, "before_update")
def _normalizar_dependencia(mapper, connection, target):
    target.nombre_normalizado = normalizar(target.nombre)


@event.listens_for(Alias, "before_insert")
@event.listens_for(Alias, "before_update")
def _normalizar_alias(mapper, connection, target):
    target.alias_normalizado = normalizar(target.alias)
