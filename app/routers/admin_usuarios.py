from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db), usuario=Depends(security.requiere_admin)):
    return crud.usuarios.listar(db)


@router.post("", response_model=schemas.UsuarioOut)
def crear_usuario(
    payload: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    if crud.usuarios.obtener_por_email(db, payload.email):
        raise HTTPException(409, "Ya existe un usuario con ese correo")
    nuevo = crud.usuarios.crear(db, payload)
    crud.auditoria.registrar(
        db, usuario.email, "usuario", nuevo.id, "CREATE",
        f"Creó usuario '{nuevo.email}' (rol={nuevo.rol.value}, área={nuevo.area or '-'})",
    )
    return nuevo
