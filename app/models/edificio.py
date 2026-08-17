from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Edificio(Base, TimestampMixin):
    __tablename__ = "edificios"

    id = Column(Integer, primary_key=True, index=True)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    direccion = Column(Text)
    pisos = Column(Integer, nullable=True)
    informacion = Column(Text)
    estado = Column(String(20), default="activo")

    sede = relationship("Sede", back_populates="edificios")
    dependencias = relationship("Dependencia", back_populates="edificio")

    def __repr__(self):
        return f"<Edificio {self.nombre}>"
