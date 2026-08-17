from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Servicio(Base, TimestampMixin):
    """Servicio puntual dentro de una dependencia (p. ej. Mesa de Partes ofrece
    'Presentación de escritos' y 'Consulta de expediente' como dos servicios
    con requisitos y canales distintos)."""

    __tablename__ = "servicios"

    id = Column(Integer, primary_key=True, index=True)
    dependencia_id = Column(Integer, ForeignKey("dependencias.id"), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    requisitos = Column(Text)
    canal = Column(String(50))  # presencial | virtual | telefonico
    horario = Column(String(300))
    costo = Column(String(100))
    duracion_estimada = Column(String(100))
    estado = Column(String(20), default="activo")

    dependencia = relationship("Dependencia", back_populates="servicios_detalle")

    def __repr__(self):
        return f"<Servicio {self.nombre}>"
