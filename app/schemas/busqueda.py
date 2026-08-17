from typing import Optional

from pydantic import BaseModel

from app.schemas.dependencia import DependenciaOut


class BusquedaRespuesta(BaseModel):
    resultados: list[DependenciaOut]
    total: int
    fallback: bool
    mensaje: Optional[str] = None
    consulta_id: Optional[int] = None


class SatisfaccionIn(BaseModel):
    valor: str  # "si" | "parcial" | "no"
