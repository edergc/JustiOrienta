from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import correo, crud, rate_limit, schemas, security
from app.config import settings
from app.database import get_db
from app.models.base import ahora_utc

router = APIRouter()


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = crud.usuarios.obtener_por_dni(db, form.username)

    # El bloqueo se revisa ANTES de validar la contraseña y sin importar si es
    # correcta: mientras dura, ni siquiera la cuenta real (que finalmente
    # recuerda su clave) debe poder saltárselo -- si no, el bloqueo protegería
    # solo contra el atacante y no serviría de nada. Una sola llamada a
    # ahora_utc(), reutilizada: con dos llamadas separadas, si el bloqueo
    # vencía justo entre una y otra, la resta podía dar un timedelta negativo
    # y el mensaje mostraba un disparate como "1440 minutos" para una cuenta
    # que ya estaba desbloqueada.
    ahora = ahora_utc()
    if usuario and usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
        minutos = max(1, -(-(usuario.bloqueado_hasta - ahora).seconds // 60))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cuenta bloqueada temporalmente por múltiples intentos fallidos. "
            f"Intenta de nuevo en {minutos} minuto(s), o pide a un(a) administrador(a) que la desbloquee.",
        )

    if not usuario or not security.verificar_password(form.password, usuario.password_hash):
        if usuario:
            crud.usuarios.registrar_intento_fallido(db, usuario)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="DNI o contraseña incorrectos",
        )
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario deshabilitado")

    crud.usuarios.resetear_intentos_fallidos(db, usuario)
    usuario.ultimo_acceso = ahora_utc()
    db.commit()

    token = security.crear_token(usuario.dni)
    return schemas.Token(access_token=token, usuario=schemas.UsuarioOut.model_validate(usuario))


@router.get("/yo", response_model=schemas.UsuarioOut)
def quien_soy(usuario=Depends(security.get_usuario_actual)):
    return usuario


@router.put("/mi-password")
def cambiar_mi_password(
    payload: schemas.CambiarPasswordIn,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    if not security.verificar_password(payload.password_actual, usuario.password_hash):
        raise HTTPException(status_code=401, detail="La contraseña actual no es correcta")
    if len(payload.password_nueva) < 6:
        raise HTTPException(status_code=422, detail="La nueva contraseña debe tener al menos 6 caracteres")
    crud.usuarios.cambiar_password(db, usuario, payload.password_nueva)
    return {"ok": True}


MENSAJE_OLVIDE_PASSWORD = (
    "Si existe una cuenta con ese DNI y tiene un correo registrado, te enviamos un enlace a ese correo."
)


@router.post("/olvide-password")
def olvide_password(payload: schemas.OlvidePasswordIn, request: Request, db: Session = Depends(get_db)):
    # Límite por DNI (evita bombardear de correos una cuenta ajena) y por IP
    # (evita probar DNIs uno por uno) -- ver app/rate_limit.py.
    ip = request.client.host if request.client else "sin-ip"
    if not rate_limit.permitido(f"olvide-dni:{payload.dni}", maximo=3, ventana_segundos=900):
        raise HTTPException(status_code=429, detail="Demasiados intentos para este DNI. Espera unos minutos.")
    if not rate_limit.permitido(f"olvide-ip:{ip}", maximo=10, ventana_segundos=900):
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espera unos minutos.")

    usuario = crud.usuarios.obtener_por_dni(db, payload.dni)
    if usuario and usuario.email:
        token = crud.usuarios.generar_solicitud_reset(db, usuario)
        enlace = f"{settings.url_publica}/admin?reset={token}"
        correo.enviar_correo_restablecer(usuario.email, usuario.nombre, enlace, crud.usuarios.MINUTOS_VIGENCIA_RESET)

    # Misma respuesta exista o no la cuenta, y tenga o no correo registrado
    # -- así nadie puede usar este endpoint para averiguar qué DNIs tienen
    # cuenta en el panel de administración.
    return {"ok": True, "mensaje": MENSAJE_OLVIDE_PASSWORD}


@router.post("/restablecer-password")
def restablecer_password(payload: schemas.RestablecerPasswordIn, db: Session = Depends(get_db)):
    usuario = crud.usuarios.obtener_por_token_reset(db, payload.token)
    if not usuario:
        raise HTTPException(status_code=400, detail="El enlace no es válido o ya expiró. Pide uno nuevo.")
    crud.usuarios.cambiar_password(db, usuario, payload.nueva_password)
    crud.usuarios.limpiar_token_reset(db, usuario)
    crud.usuarios.resetear_intentos_fallidos(db, usuario)
    return {"ok": True}
