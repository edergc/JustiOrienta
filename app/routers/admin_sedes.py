from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.SedeOut])
def listar_sedes(db: Session = Depends(get_db), usuario=Depends(security.get_usuario_actual)):
    return crud.sedes.listar(db, incluir_inactivas=(usuario.rol.value == "admin"))


@router.post("", response_model=schemas.SedeOut)
def crear_sede(
    payload: schemas.SedeCreate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    sede = crud.sedes.crear(db, payload)
    crud.auditoria.registrar(db, usuario.email, "sede", sede.id, "CREATE", f"Creó sede '{sede.nombre}'")
    return sede


@router.put("/{sede_id}", response_model=schemas.SedeOut)
def actualizar_sede(
    sede_id: int,
    payload: schemas.SedeUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    sede = crud.sedes.obtener(db, sede_id)
    if not sede:
        raise HTTPException(404, "Sede no encontrada")
    sede = crud.sedes.actualizar(db, sede, payload)
    crud.auditoria.registrar(db, usuario.email, "sede", sede.id, "UPDATE", f"Actualizó sede '{sede.nombre}'")
    return sede
