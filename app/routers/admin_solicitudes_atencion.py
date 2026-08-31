"""Gestión de "Solicitar que me llamen o me escriban" (Fase 4): el
ciudadano deja un pedido con un dato de contacto (ver app/routers/public.py,
POST /solicitudes-atencion) y aquí el panel le da seguimiento -- asignar un
área, cambiar de estado, dejar una nota interna. Mount point:
/api/v1/admin/solicitudes-atencion."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.SolicitudAtencionOut])
def listar_solicitudes(
    estado: Optional[str] = None,
    area: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_lectura_auditoria),
):
    return crud.solicitud_atencion.listar(db, estado=estado, area=area)


@router.put("/{solicitud_id}", response_model=schemas.SolicitudAtencionOut)
def actualizar_solicitud(
    solicitud_id: int,
    payload: schemas.SolicitudAtencionUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    solicitud = crud.solicitud_atencion.obtener(db, solicitud_id)
    if not solicitud:
        raise HTTPException(404, "Solicitud no encontrada")
    solicitud = crud.solicitud_atencion.actualizar(db, solicitud, payload)
    crud.auditoria.registrar(
        db, usuario.dni, "solicitud_atencion", solicitud.id, "UPDATE",
        f"Actualizo '{solicitud.codigo}' a estado '{solicitud.estado}'"
        + (f", area '{solicitud.area}'" if payload.area else ""),
    )
    return solicitud
