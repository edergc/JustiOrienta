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


def _validar_password_minima(v: str) -> str:
    # Misma regla que el autoservicio (PUT /auth/mi-password) -- antes de
    # este cambio, un(a) admin podía crear o restablecer una contraseña de
    # un solo carácter, sin ninguna validación.
    if len(v) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres")
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
    _validar_password = field_validator("password")(_validar_password_minima)


class UsuarioUpdate(BaseModel):
    nombre: str
    rol: Rol
    area: Optional[str] = None
    activo: bool = True
    nueva_password: Optional[str] = None  # solo si un(a) admin quiere restablecerla

    @field_validator("nueva_password")
    @classmethod
    def _validar_nueva_password(cls, v: Optional[str]) -> Optional[str]:
        return _validar_password_minima(v) if v else v


class CambiarPasswordIn(BaseModel):
    password_actual: str
    password_nueva: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
