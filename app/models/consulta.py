from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.models.base import Base, ahora_utc


class ConsultaLog(Base):
    """Registro anónimo de uso -- sin datos personales, solo el texto de la
    consulta y metadatos agregables. Sostiene los indicadores de uso,
    accesibilidad y eficiencia de la Fase 4 (sección 30 del proyecto)."""

    __tablename__ = "consulta_log"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(300))
    encontrado = Column(Boolean, default=False)
    # "si" | "parcial" | "no" | NULL (nadie respondió). Igual de anónimo que
    # el resto: no se une a ninguna sesión ni identificador de persona.
    satisfaccion = Column(String(10), nullable=True)
    fecha = Column(DateTime, default=ahora_utc, index=True)

    # ── Indicadores de uso y accesibilidad (sección 30) ──
    # A qué sede/dependencia se refería -- para poder desglosar "consultas
    # por sede/área/dependencia". Nunca a una persona: sigue siendo anónimo.
    sede_contexto_id = Column(Integer, ForeignKey("sedes.id"), nullable=True, index=True)
    dependencia_resultado_id = Column(Integer, ForeignKey("dependencias.id"), nullable=True, index=True)
    # Si la persona tenía activo alto contraste, texto ampliado o tema oscuro
    # al momento de buscar (indicador de uso de modo accesible).
    modo_accesible = Column(Boolean, default=False)
    # Si la consulta llegó por el micrófono (reconocimiento de voz).
    via_voz = Column(Boolean, default=False)
    # Si la consulta preguntaba por accesibilidad (rampa, ascensor, ruta
    # accesible...) -- para el indicador "consultas sobre rutas accesibles".
    sobre_accesibilidad = Column(Boolean, default=False)
