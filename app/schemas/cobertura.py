from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class SolicitudCoberturaCreate(BaseModel):
    query_text: str
    area: Optional[str] = None
    comentario: Optional[str] = None


class SolicitudCoberturaUpdate(BaseModel):
    area: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "resuelto"]] = None
    comentario: Optional[str] = None


class SolicitudCoberturaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query_text: str
    area: Optional[str] = None
    estado: str
    comentario: Optional[str] = None
    creado_por: Optional[str] = None
    creado_en: datetime
    actualizado_en: datetime
