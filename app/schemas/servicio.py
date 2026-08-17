from typing import Optional

from pydantic import BaseModel, ConfigDict


class ServicioBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    requisitos: Optional[str] = None
    canal: Optional[str] = None
    horario: Optional[str] = None
    costo: Optional[str] = None
    duracion_estimada: Optional[str] = None
    estado: str = "activo"


class ServicioCreate(ServicioBase):
    pass


class ServicioUpdate(ServicioBase):
    pass


class ServicioOut(ServicioBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dependencia_id: int
