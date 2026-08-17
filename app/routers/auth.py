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
    if not usuario or not security.verificar_password(form.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="DNI o contraseña incorrectos",
        )
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario deshabilitado")

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
