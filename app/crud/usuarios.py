from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas, security


def obtener_por_email(db: Session, email: str) -> Optional[models.Usuario]:
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()


def obtener(db: Session, usuario_id: int) -> Optional[models.Usuario]:
    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()


def listar(db: Session) -> list[models.Usuario]:
    return db.query(models.Usuario).order_by(models.Usuario.nombre).all()


def crear(db: Session, data: schemas.UsuarioCreate) -> models.Usuario:
    usuario = models.Usuario(
        nombre=data.nombre,
        email=data.email,
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
    db.commit()
    db.refresh(usuario)
    return usuario


def cambiar_password(db: Session, usuario: models.Usuario, password_nueva: str) -> None:
    usuario.password_hash = security.hash_password(password_nueva)
    db.commit()
