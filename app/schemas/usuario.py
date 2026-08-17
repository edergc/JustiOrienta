from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models import Rol


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    email: str
    rol: Rol
    area: Optional[str] = None
    activo: bool
    ultimo_acceso: Optional[datetime] = None


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: Rol = Rol.gestor
    area: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
