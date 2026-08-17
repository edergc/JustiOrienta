from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.EdificioOut])
def listar_edificios(
    sede_id: Optional[int] = None,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    return crud.edificios.listar(db, sede_id=sede_id)


@router.post("", response_model=schemas.EdificioOut)
def crear_edificio(
    payload: schemas.EdificioCreate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    if not crud.sedes.obtener(db, payload.sede_id):
        raise HTTPException(404, "La sede indicada no existe")
    edificio = crud.edificios.crear(db, payload)
    crud.auditoria.registrar(db, usuario.dni, "edificio", edificio.id, "CREATE", f"Creó edificio '{edificio.nombre}'")
    return edificio


@router.put("/{edificio_id}", response_model=schemas.EdificioOut)
def actualizar_edificio(
    edificio_id: int,
    payload: schemas.EdificioUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    edificio = crud.edificios.obtener(db, edificio_id)
    if not edificio:
        raise HTTPException(404, "Edificio no encontrado")
    if not crud.sedes.obtener(db, payload.sede_id):
        raise HTTPException(404, "La sede indicada no existe")
    edificio = crud.edificios.actualizar(db, edificio, payload)
    crud.auditoria.registrar(db, usuario.dni, "edificio", edificio.id, "UPDATE", f"Actualizó edificio '{edificio.nombre}'")
    return edificio
