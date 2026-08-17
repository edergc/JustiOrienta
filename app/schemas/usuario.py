import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import Rol

_DNI_RE = re.compile(r"^\d{8}$")


def _validar_dni(v: str) -> str:
    if not _DNI_RE.match(v):
        raise ValueError("El DNI debe tener exactamente 8 dígitos numéricos")
    return v


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    dni: str
    rol: Rol
    area: Optional[str] = None
    activo: bool
    ultimo_acceso: Optional[datetime] = None


class UsuarioCreate(BaseModel):
    nombre: str
    dni: str
    password: str
    rol: Rol = Rol.gestor
    area: Optional[str] = None

    _validar_dni = field_validator("dni")(_validar_dni)


class UsuarioUpdate(BaseModel):
    nombre: str
    rol: Rol
    area: Optional[str] = None
    activo: bool = True
    nueva_password: Optional[str] = None  # solo si un(a) admin quiere restablecerla


class CambiarPasswordIn(BaseModel):
    password_actual: str
    password_nueva: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
