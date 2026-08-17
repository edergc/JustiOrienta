from sqlalchemy import Column, DateTime, Integer, String, Text

from app.models.base import Base, ahora_utc


class Auditoria(Base):
    """Registro de quién cambió qué. entidad+entidad_id identifican el
    registro afectado (p. ej. entidad='dependencia', entidad_id=12)."""

    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_email = Column(String(150))
    entidad = Column(String(30), index=True)  # dependencia | servicio | sede | edificio | usuario
    entidad_id = Column(Integer, nullable=True, index=True)
    accion = Column(String(20))  # CREATE | UPDATE | APROBAR | RECHAZAR | DELETE
    detalle = Column(Text)
    fecha = Column(DateTime, default=ahora_utc, index=True)
