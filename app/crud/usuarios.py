from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas, security
from app.models.base import ahora_utc

MAX_INTENTOS_FALLIDOS = 5
MINUTOS_BLOQUEO = 15


def obtener_por_dni(db: Session, dni: str) -> Optional[models.Usuario]:
    return db.query(models.Usuario).filter(models.Usuario.dni == dni).first()


def obtener(db: Session, usuario_id: int) -> Optional[models.Usuario]:
    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()


def listar(db: Session) -> list[models.Usuario]:
    return db.query(models.Usuario).order_by(models.Usuario.nombre).all()


def crear(db: Session, data: schemas.UsuarioCreate) -> models.Usuario:
    usuario = models.Usuario(
        nombre=data.nombre,
        dni=data.dni,
        password_hash=security.hash_password(data.password),
        rol=data.rol,
        area=data.area,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def actualizar(db: Session, usuario: models.Usuario, data: schemas.UsuarioUpdate) -> models.Usuario:
    usuario.nombre = data.nombre
    usuario.rol = data.rol
    usuario.area = data.area
    usuario.activo = data.activo
    if data.nueva_password:
        usuario.password_hash = security.hash_password(data.nueva_password)
    # Un(a) admin guardando cambios en la cuenta es, de por sí, la revisión
    # humana que un bloqueo automático espera -- se levanta aquí para no dejar
    # a alguien esperando los MINUTOS_BLOQUEO después de que admin ya intervino.
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    db.commit()
    db.refresh(usuario)
    return usuario


def cambiar_password(db: Session, usuario: models.Usuario, password_nueva: str) -> None:
    usuario.password_hash = security.hash_password(password_nueva)
    db.commit()


def registrar_intento_fallido(db: Session, usuario: models.Usuario) -> None:
    """Tras MAX_INTENTOS_FALLIDOS seguidos, bloquea el login de esta cuenta por
    MINUTOS_BLOQUEO -- protección contra fuerza bruta ya que el DNI (usuario de
    acceso) es un dato público, no un secreto."""
    usuario.intentos_fallidos += 1
    if usuario.intentos_fallidos >= MAX_INTENTOS_FALLIDOS:
        usuario.bloqueado_hasta = ahora_utc() + timedelta(minutes=MINUTOS_BLOQUEO)
    db.commit()


def resetear_intentos_fallidos(db: Session, usuario: models.Usuario) -> None:
    if usuario.intentos_fallidos or usuario.bloqueado_hasta:
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        db.commit()
