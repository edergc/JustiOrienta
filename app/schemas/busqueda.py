from typing import Optional

from pydantic import BaseModel

from app.schemas.dependencia import DependenciaOut
from app.schemas.sede import SedeOut


class BusquedaRespuesta(BaseModel):
    resultados: list[DependenciaOut]
    total: int
    fallback: bool
    mensaje: Optional[str] = None
    consulta_id: Optional[int] = None
    # Se llena cuando la consulta preguntaba por accesibilidad (rampa,
    # ascensor...) y se conoce la sede por contexto (?sede= en la URL) --
    # responde directo desde los booleanos de la sede, sin listar dependencias.
    sede_accesibilidad: Optional[SedeOut] = None
    # Etiquetas de perfil detectadas dentro de la consulta (ej. "adulto
    # mayor", "silla de ruedas") -- ver app/nlp.py: detectar_senales_perfil.
    # Nunca cambia QUÉ se muestra, solo permite que el frontend resalte la
    # información de accesibilidad que la tarjeta ya iba a mostrar.
    senales_perfil: list[str] = []


class SatisfaccionIn(BaseModel):
    valor: str  # "si" | "parcial" | "no"
