from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, schemas, security
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
