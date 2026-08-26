"""CRUD del mapa interno (wayfinding auto-declarado, Fase 4): nodos
reconocibles y las conexiones entre ellos. Mount point: /api/v1/admin/mapa.
Solo admin -- es infraestructura tecnica de la sede, no contenido propio de
un area (a diferencia de las dependencias)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db

router = APIRouter()


@router.get("/nodos", response_model=list[schemas.NodoOut])
def listar_nodos(
    sede_id: int,
    piso: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    return crud.mapa.listar_nodos(db, sede_id, piso)


@router.post("/nodos", response_model=schemas.NodoOut)
def crear_nodo(
    payload: schemas.NodoCreate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    nodo = crud.mapa.crear_nodo(db, payload)
    crud.auditoria.registrar(db, usuario.dni, "nodo_ubicacion", nodo.id, "CREATE", f"Creo el nodo '{nodo.nombre}'")
    return nodo


@router.put("/nodos/{nodo_id}", response_model=schemas.NodoOut)
def actualizar_nodo(
    nodo_id: int,
    payload: schemas.NodoUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    nodo = crud.mapa.obtener_nodo(db, nodo_id)
    if not nodo:
        raise HTTPException(404, "Nodo no encontrado")
    nodo = crud.mapa.actualizar_nodo(db, nodo, payload)
    crud.auditoria.registrar(db, usuario.dni, "nodo_ubicacion", nodo.id, "UPDATE", f"Actualizo el nodo '{nodo.nombre}'")
    return nodo


@router.delete("/nodos/{nodo_id}")
def eliminar_nodo(
    nodo_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    nodo = crud.mapa.obtener_nodo(db, nodo_id)
    if not nodo:
        raise HTTPException(404, "Nodo no encontrado")
    crud.auditoria.registrar(db, usuario.dni, "nodo_ubicacion", nodo.id, "DELETE", f"Elimino el nodo '{nodo.nombre}'")
    crud.mapa.eliminar_nodo(db, nodo)
    return {"ok": True}


@router.get("/conexiones", response_model=list[schemas.ConexionOut])
def listar_conexiones(
    sede_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    return crud.mapa.listar_conexiones(db, sede_id)


@router.post("/conexiones", response_model=schemas.ConexionOut)
def crear_conexion(
    payload: schemas.ConexionCreate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    if not crud.mapa.obtener_nodo(db, payload.nodo_a_id) or not crud.mapa.obtener_nodo(db, payload.nodo_b_id):
        raise HTTPException(404, "Uno de los dos nodos indicados no existe")
    conexion = crud.mapa.crear_conexion(db, payload)
    crud.auditoria.registrar(
        db, usuario.dni, "conexion_nodo", conexion.id, "CREATE",
        f"Conecto el nodo {conexion.nodo_a_id} con el nodo {conexion.nodo_b_id}",
    )
    return conexion


@router.put("/conexiones/{conexion_id}", response_model=schemas.ConexionOut)
def actualizar_conexion(
    conexion_id: int,
    payload: schemas.ConexionUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    conexion = crud.mapa.obtener_conexion(db, conexion_id)
    if not conexion:
        raise HTTPException(404, "Conexión no encontrada")
    conexion = crud.mapa.actualizar_conexion(db, conexion, payload)
    crud.auditoria.registrar(db, usuario.dni, "conexion_nodo", conexion.id, "UPDATE", "Actualizo la conexion")
    return conexion


@router.delete("/conexiones/{conexion_id}")
def eliminar_conexion(
    conexion_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_admin),
):
    conexion = crud.mapa.obtener_conexion(db, conexion_id)
    if not conexion:
        raise HTTPException(404, "Conexión no encontrada")
    crud.auditoria.registrar(db, usuario.dni, "conexion_nodo", conexion.id, "DELETE", "Elimino la conexion")
    crud.mapa.eliminar_conexion(db, conexion)
    return {"ok": True}
