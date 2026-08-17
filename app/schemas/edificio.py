from typing import Optional

from pydantic import BaseModel, ConfigDict


class EdificioBase(BaseModel):
    sede_id: int
    nombre: str
    direccion: Optional[str] = None
    pisos: Optional[int] = None
    informacion: Optional[str] = None
    estado: str = "activo"


class EdificioCreate(EdificioBase):
    pass


class EdificioUpdate(EdificioBase):
    pass


class EdificioOut(EdificioBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
