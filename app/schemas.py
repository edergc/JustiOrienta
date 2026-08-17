from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DependenciaBase(BaseModel):
    tipo: str
    categoria: Optional[str] = None
    nombre: str
    sede: Optional[str] = None
    edificio: Optional[str] = None
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
    actualizado_en: Optional[datetime] = None


class BusquedaResultado(BaseModel):
    dependencia: DependenciaOut
    fallback: bool = False


class BusquedaRespuesta(BaseModel):
    resultados: list[DependenciaOut]
    total: int
    fallback: bool
    mensaje: Optional[str] = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    email: str
    rol: str
    area: Optional[str] = None
    activo: bool


class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    password: str
    rol: str = "gestor"
    area: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class AuditoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario_email: Optional[str] = None
    dependencia_id: Optional[int] = None
    accion: str
    detalle: Optional[str] = None
    fecha: datetime
