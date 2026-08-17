from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuditoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario_email: Optional[str] = None
    entidad: Optional[str] = None
    entidad_id: Optional[int] = None
    accion: str
    detalle: Optional[str] = None
    fecha: datetime
