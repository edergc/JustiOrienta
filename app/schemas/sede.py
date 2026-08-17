from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class SedeBase(BaseModel):
    nombre: str
    nombre_corto: Optional[str] = None
    direccion: Optional[str] = None
    referencia: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    horario_atencion: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    rampa: bool = False
    ascensor: bool = False
    banio_accesible: bool = False
    estacionamiento_accesible: bool = False
    personal_asistencia: bool = False
    estado: Literal["activo", "inactivo"] = "activo"


class SedeCreate(SedeBase):
    pass


class SedeUpdate(SedeBase):
    pass


class SedeOut(SedeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
