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
    if crud.usuarios.obtener_por_dni(db, payload.dni):
        raise HTTPException(409, "Ya existe un usuario con ese DNI")
    nuevo = crud.usuarios.crear(db, payload)
    crud.auditoria.registrar(
        db, usuario.dni, "usuario", nuevo.id, "CREATE",
        f"Creó usuario '{nuevo.nombre}' (DNI {nuevo.dni}, rol={nuevo.rol.value}, área={nuevo.area or '-'})",
    )
    return nuevo


@router.put("/{usuario_id}", response_model=schemas.UsuarioOut)
def actualizar_usuario(
    usuario_id: int,
    payload: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    objetivo = crud.usuarios.obtener(db, usuario_id)
    if not objetivo:
        raise HTTPException(404, "Usuario no encontrado")
    if objetivo.id == usuario.id and not payload.activo:
        raise HTTPException(400, "No puedes desactivar tu propia cuenta")

    detalle = f"rol={payload.rol.value}, área={payload.area or '-'}, activo={payload.activo}"
    if payload.nueva_password:
        detalle += ", contraseña restablecida"
    objetivo = crud.usuarios.actualizar(db, objetivo, payload)
    crud.auditoria.registrar(db, usuario.dni, "usuario", objetivo.id, "UPDATE", detalle)
    return objetivo
