"""Autenticación: hash de contraseñas (bcrypt) y tokens (JWT). Todo con librerías
libres (passlib, python-jose) -- sin servicios de terceros ni costo."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models
from app.models import Rol

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Únicas rutas que alguien con debe_cambiar_password=True puede seguir usando
# -- ver el propio cambio de contraseña, y consultar quién es (lo necesita el
# panel para saber que tiene que abrir el modal obligatorio). Todo lo demás
# queda bloqueado hasta que la persona elija su propia contraseña.
_RUTAS_PERMITIDAS_CON_PASSWORD_PENDIENTE = {"/api/v1/auth/mi-password", "/api/v1/auth/yo"}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def crear_token(dni: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.token_expire_minutes)
    payload = {"sub": dni, "exp": expira}
    return jwt.encode(payload, settings.justicia_orienta_secret, algorithm=ALGORITHM)


def get_usuario_actual(
    request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.Usuario:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o sesión expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.justicia_orienta_secret, algorithms=[ALGORITHM])
        dni: Optional[str] = payload.get("sub")
        if dni is None:
            raise credenciales_invalidas
    except JWTError:
        raise credenciales_invalidas

    usuario = db.query(models.Usuario).filter(models.Usuario.dni == dni).first()
    if usuario is None or not usuario.activo:
        raise credenciales_invalidas

    if usuario.debe_cambiar_password and request.url.path not in _RUTAS_PERMITIDAS_CON_PASSWORD_PENDIENTE:
        raise HTTPException(status_code=403, detail="Debes cambiar tu contraseña antes de continuar")

    return usuario


def requiere_admin(usuario: models.Usuario = Depends(get_usuario_actual)) -> models.Usuario:
    if usuario.rol != Rol.admin:
        raise HTTPException(status_code=403, detail="Requiere rol de administrador")
    return usuario


def requiere_lectura_auditoria(usuario: models.Usuario = Depends(get_usuario_actual)) -> models.Usuario:
    if usuario.rol not in (Rol.admin, Rol.auditor):
        raise HTTPException(status_code=403, detail="Requiere rol de administrador o auditor")
    return usuario


def requiere_lectura_reportes(usuario: models.Usuario = Depends(get_usuario_actual)) -> models.Usuario:
    """Igual que requiere_lectura_auditoria pero también admite el rol
    'consulta' -- puede ver indicadores/reportes, pero no el detalle de quién
    cambió qué (eso sigue siendo solo admin/auditor)."""
    if usuario.rol not in (Rol.admin, Rol.auditor, Rol.consulta):
        raise HTTPException(status_code=403, detail="Requiere rol de administrador, auditor o consulta")
    return usuario


def puede_editar_area(usuario: models.Usuario, area: Optional[str]) -> bool:
    """Admin edita cualquier área. Gestor/validador solo la propia."""
    if usuario.rol == Rol.admin:
        return True
    if usuario.rol in (Rol.gestor, Rol.validador):
        return bool(usuario.area) and usuario.area == area
    return False


def puede_aprobar(usuario: models.Usuario, area: Optional[str]) -> bool:
    """Solo admin o el/la validador/a de esa misma área puede publicar."""
    if usuario.rol == Rol.admin:
        return True
    if usuario.rol == Rol.validador:
        return bool(usuario.area) and usuario.area == area
    return False
