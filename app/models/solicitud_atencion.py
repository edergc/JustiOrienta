from sqlalchemy import Column, Integer, String, Text

from app.models.base import Base, TimestampMixin


class SolicitudAtencion(Base, TimestampMixin):
    """"Solicitar que me llamen o me escriban" (Fase 4, item 6 del backlog
    de v2.0): un salto real de "buscador" a "atención" sin necesitar chat en
    vivo ni videollamada -- el ciudadano deja su pedido, alguien del área
    correspondiente lo contacta después. Mismo espíritu que
    SolicitudCobertura (asignar a un área, dar seguimiento), pero esta la
    origina directamente el ciudadano, con datos de contacto, no un(a)
    admin triando una búsqueda fallida.

    codigo es lo único que el ciudadano necesita guardar para consultar el
    estado después -- no requiere cuenta ni contraseña."""

    __tablename__ = "solicitudes_atencion"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=False)

    nombre_contacto = Column(String(200), nullable=False)
    telefono = Column(String(50), nullable=True)
    correo = Column(String(200), nullable=True)
    motivo = Column(Text, nullable=False)

    area = Column(String(150), index=True, nullable=True)
    # recibida -> derivada -> en_atencion -> respondida -> cerrada
    estado = Column(String(20), default="recibida", index=True)
    comentario = Column(Text, nullable=True)

    def __repr__(self):
        return f"<SolicitudAtencion {self.codigo} ({self.estado})>"
