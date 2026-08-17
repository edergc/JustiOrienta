"""Autenticación: hash de contraseñas (bcrypt) y tokens (JWT). Todo con librerías
libres (passlib, python-jose) -- sin servicios de terceros ni costo."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
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


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def crear_token(email: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.token_expire_minutes)
    payload = {"sub": email, "exp": expira}
    return jwt.encode(payload, settings.justicia_orienta_secret, algorithm=ALGORITHM)


def get_usuario_actual(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.Usuario:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o sesión expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.justicia_orienta_secret, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credenciales_invalidas
    except JWTError:
        raise credenciales_invalidas

    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if usuario is None or not usuario.activo:
        raise credenciales_invalidas
    return usuario


def requiere_admin(usuario: models.Usuario = Depends(get_usuario_actual)) -> models.Usuario:
    if usuario.rol != Rol.admin:
        raise HTTPException(status_code=403, detail="Requiere rol de administrador")
    return usuario


def requiere_lectura_auditoria(usuario: models.Usuario = Depends(get_usuario_actual)) -> models.Usuario:
    if usuario.rol not in (Rol.admin, Rol.auditor):
        raise HTTPException(status_code=403, detail="Requiere rol de administrador o auditor")
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
