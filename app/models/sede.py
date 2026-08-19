from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Sede(Base, TimestampMixin):
    __tablename__ = "sedes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), unique=True, nullable=False, index=True)
    nombre_corto = Column(String(100))
    direccion = Column(Text)
    referencia = Column(Text)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    horario_atencion = Column(String(300))
    telefono = Column(String(150))
    correo = Column(String(150))

    # Accesibilidad general de la sede (una dependencia puntual puede además
    # tener sus propias condiciones -- ver Dependencia).
    rampa = Column(Boolean, default=False)
    ascensor = Column(Boolean, default=False)
    banio_accesible = Column(Boolean, default=False)
    estacionamiento_accesible = Column(Boolean, default=False)
    personal_asistencia = Column(Boolean, default=False)

    estado = Column(String(20), default="activo")  # activo | inactivo

    edificios = relationship("Edificio", back_populates="sede", cascade="all, delete-orphan")
    dependencias = relationship("Dependencia", back_populates="sede")

    def __repr__(self):
        return f"<Sede {self.nombre}>"
