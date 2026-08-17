from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.models.base import Base, ahora_utc


class ConsultaLog(Base):
    """Registro anónimo de uso -- sin datos personales, solo el texto de la
    consulta y si encontró algo. Sostiene los indicadores de la Fase 4."""

    __tablename__ = "consulta_log"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(300))
    encontrado = Column(Boolean, default=False)
    # "si" | "parcial" | "no" | NULL (nadie respondió). Igual de anónimo que
    # el resto: no se une a ninguna sesión ni identificador de persona.
    satisfaccion = Column(String(10), nullable=True)
    fecha = Column(DateTime, default=ahora_utc, index=True)
