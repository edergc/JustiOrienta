from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.models.base import Base, ahora_utc


class ConsultaLog(Base):
    """Registro anónimo de uso -- sin datos personales, solo el texto de la
    consulta y si encontró algo. Sostiene los indicadores de la Fase 4."""

    __tablename__ = "consulta_log"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(300))
    encontrado = Column(Boolean, default=False)
    fecha = Column(DateTime, default=ahora_utc, index=True)
