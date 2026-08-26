from sqlalchemy import Column, Integer, String, Text

from app.models.base import Base, TimestampMixin


class SolicitudCobertura(Base, TimestampMixin):
    """Cierra el ciclo del motor de descubrimiento (Fase 4): una búsqueda
    que la gente repite y el catálogo no resuelve se asigna a mano a un
    área responsable, con seguimiento -- en vez de quedar solo como un
    número más en "top búsquedas sin resultado". Deliberadamente manual:
    el proyecto no adivina a qué área pertenece un texto libre, una
    persona lo decide y queda su nombre en auditoría."""

    __tablename__ = "solicitudes_cobertura"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(300), nullable=False)
    area = Column(String(150), index=True)
    estado = Column(String(20), default="pendiente", index=True)  # pendiente | en_progreso | resuelto
    comentario = Column(Text, nullable=True)
    creado_por = Column(String(8))

    def __repr__(self):
        return f"<SolicitudCobertura {self.query_text!r} -> {self.area}>"
