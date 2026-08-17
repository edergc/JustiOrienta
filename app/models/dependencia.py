from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, event
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, normalizar


class Dependencia(Base, TimestampMixin):
    __tablename__ = "dependencias"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(30), nullable=False, index=True)  # jurisdiccional | administrativa | servicio
    categoria = Column(String(100))
    nombre = Column(String(200), nullable=False)
    nombre_normalizado = Column(String(200), index=True)

    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False, index=True)
    edificio_id = Column(Integer, ForeignKey("edificios.id"), nullable=True)
    piso = Column(String(30))
    oficina = Column(String(50))

    horario = Column(String(300))
    servicios = Column(Text)  # resumen breve; el detalle estructurado vive en Servicio
    requisitos = Column(Text)
    telefono = Column(String(40))
    correo = Column(String(150))

    # Accesibilidad específica de esta dependencia (puede diferir de la sede:
    # p. ej. la sede tiene ascensor, pero esta oficina puntual no es accesible).
    rampa = Column(Boolean, default=False)
    ascensor = Column(Boolean, default=False)
    banio_accesible = Column(Boolean, default=False)
    ruta_accesible = Column(Boolean, default=False)

    estado = Column(String(20), default="revision", index=True)  # revision | activo | inactivo
    area = Column(String(150), index=True)  # límite de permisos para gestor/validador
    responsable_validar = Column(String(200))

    sede = relationship("Sede", back_populates="dependencias")
    edificio = relationship("Edificio", back_populates="dependencias")
    alias = relationship("Alias", back_populates="dependencia", cascade="all, delete-orphan")
    servicios_detalle = relationship(
        "Servicio", back_populates="dependencia", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Dependencia {self.nombre}>"


@event.listens_for(Dependencia, "before_insert")
@event.listens_for(Dependencia, "before_update")
def _normalizar_dependencia(mapper, connection, target):
    target.nombre_normalizado = normalizar(target.nombre)
