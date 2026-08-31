from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from app.models.base import Base, ahora_utc


class Auditoria(Base):
    """Registro de quién cambió qué. entidad+entidad_id identifican el
    registro afectado (p. ej. entidad='dependencia', entidad_id=12)."""

    __tablename__ = "auditoria"
    # Único índice sobre estas dos columnas: la única consulta real
    # (crud.auditoria.listar_por_entidad) siempre filtra ambas juntas, nunca
    # entidad_id sola -- un índice compuesto la sirve igual de bien que dos
    # índices separados, con menos costo de escritura en cada inserción.
    __table_args__ = (Index("ix_auditoria_entidad_entidad_id", "entidad", "entidad_id"),)

    id = Column(Integer, primary_key=True, index=True)
    usuario_dni = Column(String(8))
    entidad = Column(String(30))  # dependencia | servicio | sede | edificio | usuario
    entidad_id = Column(Integer, nullable=True)
    accion = Column(String(20))  # CREATE | UPDATE | APROBAR | RECHAZAR | DELETE
    detalle = Column(Text)
    fecha = Column(DateTime, default=ahora_utc, index=True)
