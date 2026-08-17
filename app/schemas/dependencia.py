from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.edificio import EdificioOut
from app.schemas.sede import SedeOut
from app.schemas.servicio import ServicioOut


class DependenciaBase(BaseModel):
    tipo: str
    categoria: Optional[str] = None
    nombre: str
    sede_id: int
    edificio_id: Optional[int] = None
    piso: Optional[str] = None
    oficina: Optional[str] = None
    horario: Optional[str] = None
    servicios: Optional[str] = None
    requisitos: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    rampa: bool = False
    ascensor: bool = False
    banio_accesible: bool = False
    ruta_accesible: bool = False
    estado: str = "revision"
    area: Optional[str] = None
    responsable_validar: Optional[str] = None


class DependenciaCreate(DependenciaBase):
    alias: str = ""  # separados por coma, igual que la plantilla Excel


class DependenciaUpdate(DependenciaCreate):
    pass


class DependenciaOut(DependenciaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alias: list[str] = []
    sede: Optional[SedeOut] = None
    edificio: Optional[EdificioOut] = None
    servicios_detalle: list[ServicioOut] = []
    actualizado_en: Optional[datetime] = None

    @field_validator("alias", mode="before")
    @classmethod
    def _alias_a_texto(cls, v):
        if v and hasattr(v[0] if len(v) else None, "alias"):
            return [a.alias for a in v]
        return v
