import re
import unicodedata
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime

from app.database import Base

__all__ = ["Base", "normalizar", "TimestampMixin", "ahora_utc"]


def ahora_utc() -> datetime:
    """UTC "naive" (sin tzinfo) -- coherente con cómo SQLite/las columnas
    DateTime ya almacenan todo en este proyecto. Reemplaza datetime.utcnow(),
    obsoleto desde Python 3.12."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalizar(texto: str) -> str:
    """minúsculas, sin tildes, sin signos, espacios simples -- usado para búsqueda."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


class TimestampMixin:
    creado_en = Column(DateTime, default=ahora_utc, nullable=False)
    actualizado_en = Column(DateTime, default=ahora_utc, onupdate=ahora_utc, nullable=False)
