from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas, security
from app.database import get_db

router = APIRouter()


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == form.username).first()
    if not usuario or not security.verificar_password(form.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario deshabilitado")

    token = security.crear_token(usuario.email)
    return schemas.Token(access_token=token, usuario=schemas.UsuarioOut.model_validate(usuario))


@router.get("/yo", response_model=schemas.UsuarioOut)
def quien_soy(usuario: models.Usuario = Depends(security.get_usuario_actual)):
    return usuario
