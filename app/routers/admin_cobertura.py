"""Solicitudes de cobertura: cierra el ciclo del motor de descubrimiento
(Fase 4) -- asigna a mano una busqueda sin resultado a un area responsable
y le da seguimiento, en vez de dejarla solo como un numero en "top
busquedas sin resultado". Mount point: /api/v1/admin/cobertura."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.SolicitudCoberturaOut])
def listar_cobertura(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_lectura_auditoria),
):
    return crud.cobertura.listar(db, estado=estado)


@router.post("", response_model=schemas.SolicitudCoberturaOut)
def crear_cobertura(
    payload: schemas.SolicitudCoberturaCreate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    solicitud = crud.cobertura.crear(db, payload, usuario.dni)
    crud.auditoria.registrar(
        db, usuario.dni, "solicitud_cobertura", solicitud.id, "CREATE",
        f"Asigno '{payload.query_text}' al area '{payload.area or 'sin asignar'}'",
    )
    return solicitud


@router.put("/{solicitud_id}", response_model=schemas.SolicitudCoberturaOut)
def actualizar_cobertura(
    solicitud_id: int,
    payload: schemas.SolicitudCoberturaUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    solicitud = crud.cobertura.obtener(db, solicitud_id)
    if not solicitud:
        raise HTTPException(404, "Solicitud no encontrada")
    solicitud = crud.cobertura.actualizar(db, solicitud, payload)
    crud.auditoria.registrar(
        db, usuario.dni, "solicitud_cobertura", solicitud.id, "UPDATE",
        f"Actualizo estado a '{solicitud.estado}'" + (f", area '{solicitud.area}'" if payload.area else ""),
    )
    return solicitud
