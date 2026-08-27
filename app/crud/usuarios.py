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
        email=data.email,
        password_hash=security.hash_password(data.password),
        rol=data.rol,
        area=data.area,
        # La contraseña la eligió admin, no la propia persona -- se exige
        # cambiarla antes de dejar usar el resto del sistema (ver
        # security.get_usuario_actual).
        debe_cambiar_password=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def actualizar(
    db: Session, usuario: models.Usuario, data: schemas.UsuarioUpdate, es_autoedicion: bool = False
) -> models.Usuario:
    usuario.nombre = data.nombre
    usuario.email = data.email
    usuario.rol = data.rol
    usuario.area = data.area
    usuario.activo = data.activo
    if data.nueva_password:
        usuario.password_hash = security.hash_password(data.nueva_password)
        if not es_autoedicion:
            # Alguien MÁS eligió esta contraseña por esta persona -- se exige
            # cambiarla. Si es admin editando su PROPIA cuenta, la eligió
            # él/ella mismo/a: forzarlo igual lo dejaría bloqueado fuera de su
            # propia sesión (403 en el siguiente clic) hasta recargar la
            # página, sin ganar nada en seguridad.
            usuario.debe_cambiar_password = True
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
    usuario.debe_cambiar_password = False  # ahora sí la eligió la propia persona
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


MINUTOS_VIGENCIA_RESET = 30


def generar_solicitud_reset(db: Session, usuario: models.Usuario) -> str:
    """Crea un token de un solo uso, vigente MINUTOS_VIGENCIA_RESET, y
    devuelve el token en texto plano (para mandarlo por correo) -- solo su
    hash queda guardado."""
    token, token_hash = security.generar_token_reset()
    usuario.reset_token_hash = token_hash
    usuario.reset_token_expira = ahora_utc() + timedelta(minutes=MINUTOS_VIGENCIA_RESET)
    db.commit()
    return token


def obtener_por_token_reset(db: Session, token: str) -> Optional[models.Usuario]:
    token_hash = security.hash_token_reset(token)
    usuario = db.query(models.Usuario).filter(models.Usuario.reset_token_hash == token_hash).first()
    if not usuario or not usuario.reset_token_expira or usuario.reset_token_expira < ahora_utc():
        return None
    return usuario


def limpiar_token_reset(db: Session, usuario: models.Usuario) -> None:
    usuario.reset_token_hash = None
    usuario.reset_token_expira = None
    db.commit()
