"""CRUD de dependencias + flujo de publicación (revisión -> aprobación) +
servicios anidados. Mount point: /api/v1/admin (ver app/main.py)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db
from app.models import Rol

router = APIRouter()


# ── Dependencias ──────────────────────────────────────────────

@router.get("/dependencias", response_model=schemas.DependenciaListaOut)
def listar_dependencias(
    estado: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limite: int = 20,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    area = None if usuario.rol == Rol.admin else usuario.area
    limite = min(limite, 100)
    deps = crud.dependencias.listar(db, area=area, estado=estado, q_nombre=q, skip=skip, limite=limite)
    total = crud.dependencias.contar(db, area=area, estado=estado, q_nombre=q)
    return schemas.DependenciaListaOut(
        items=[schemas.DependenciaOut.model_validate(d) for d in deps],
        total=total, skip=skip, limite=limite,
    )


@router.post("/dependencias", response_model=schemas.DependenciaOut)
def crear_dependencia(
    payload: schemas.DependenciaCreate,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    if not security.puede_editar_area(usuario, payload.area):
        raise HTTPException(403, "Solo puedes crear dependencias dentro de tu propia área")

    data = payload.model_dump(exclude={"alias"})
    if usuario.rol != Rol.admin:
        # Nadie que no sea admin publica directamente: toda creación entra a revisión.
        data["estado"] = "revision"

    dep = crud.dependencias.crear(db, data, payload.alias)
    crud.auditoria.registrar(db, usuario.email, "dependencia", dep.id, "CREATE", f"Creó '{dep.nombre}'")
    return schemas.DependenciaOut.model_validate(dep)


@router.put("/dependencias/{dep_id}", response_model=schemas.DependenciaOut)
def actualizar_dependencia(
    dep_id: int,
    payload: schemas.DependenciaUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not security.puede_editar_area(usuario, dep.area):
        raise HTTPException(403, "No tienes permiso para editar esta dependencia")

    data = payload.model_dump(exclude={"alias"})
    if data.get("estado") == "activo" and not security.puede_aprobar(usuario, dep.area):
        # No se rechaza el guardado por esto: un(a) gestor(a) corrigiendo un
        # dato de algo ya publicado no debería toparse con un 403 solo porque
        # el formulario reenvía el estado actual. En cambio, cualquier edición
        # de gestor(a) vuelve a pasar por revisión -- así ningún cambio de
        # contenido llega al público sin que alguien con permiso lo revise.
        data["estado"] = "revision"

    cambios = []
    for k, v in data.items():
        if getattr(dep, k) != v:
            cambios.append(f"{k}: '{getattr(dep, k)}' -> '{v}'")

    dep = crud.dependencias.actualizar(db, dep, data, payload.alias)
    crud.auditoria.registrar(
        db, usuario.email, "dependencia", dep.id, "UPDATE", "; ".join(cambios) or "Sin cambios detectados"
    )
    return schemas.DependenciaOut.model_validate(dep)


@router.post("/dependencias/{dep_id}/aprobar", response_model=schemas.DependenciaOut)
def aprobar_dependencia(
    dep_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not security.puede_aprobar(usuario, dep.area):
        raise HTTPException(403, "Solo un(a) validador(a) de esta área o un(a) administrador(a) puede aprobar")
    if dep.estado != "revision":
        raise HTTPException(400, f"Solo se puede aprobar contenido en revisión (estado actual: {dep.estado})")

    dep = crud.dependencias.aprobar(db, dep)
    crud.auditoria.registrar(db, usuario.email, "dependencia", dep.id, "APROBAR", f"Publicó '{dep.nombre}'")
    return schemas.DependenciaOut.model_validate(dep)


@router.post("/dependencias/{dep_id}/rechazar", response_model=schemas.DependenciaOut)
def rechazar_dependencia(
    dep_id: int,
    comentario: str = "",
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not security.puede_aprobar(usuario, dep.area):
        raise HTTPException(403, "Solo un(a) validador(a) de esta área o un(a) administrador(a) puede rechazar")

    dep = crud.dependencias.enviar_a_revision(db, dep)
    detalle = f"Devolvió a revisión '{dep.nombre}'" + (f": {comentario}" if comentario else "")
    crud.auditoria.registrar(db, usuario.email, "dependencia", dep.id, "RECHAZAR", detalle)
    return schemas.DependenciaOut.model_validate(dep)


@router.delete("/dependencias/{dep_id}")
def desactivar_dependencia(
    dep_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not security.puede_editar_area(usuario, dep.area):
        raise HTTPException(403, "No tienes permiso para modificar esta dependencia")

    crud.dependencias.desactivar(db, dep)
    crud.auditoria.registrar(db, usuario.email, "dependencia", dep.id, "DELETE", f"Desactivó '{dep.nombre}'")
    return {"ok": True}


# ── Servicios anidados ────────────────────────────────────────

@router.get("/dependencias/{dep_id}/servicios", response_model=list[schemas.ServicioOut])
def listar_servicios(
    dep_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    return crud.servicios.listar_por_dependencia(db, dep_id)


@router.post("/dependencias/{dep_id}/servicios", response_model=schemas.ServicioOut)
def crear_servicio(
    dep_id: int,
    payload: schemas.ServicioCreate,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not security.puede_editar_area(usuario, dep.area):
        raise HTTPException(403, "No tienes permiso para editar los servicios de esta dependencia")

    servicio = crud.servicios.crear(db, dep_id, payload)
    crud.auditoria.registrar(db, usuario.email, "servicio", servicio.id, "CREATE", f"Creó servicio '{servicio.nombre}' en '{dep.nombre}'")
    return servicio


@router.put("/servicios/{servicio_id}", response_model=schemas.ServicioOut)
def actualizar_servicio(
    servicio_id: int,
    payload: schemas.ServicioUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    servicio = crud.servicios.obtener(db, servicio_id)
    if not servicio:
        raise HTTPException(404, "Servicio no encontrado")
    dep = crud.dependencias.obtener(db, servicio.dependencia_id)
    if not security.puede_editar_area(usuario, dep.area):
        raise HTTPException(403, "No tienes permiso para editar este servicio")

    servicio = crud.servicios.actualizar(db, servicio, payload)
    crud.auditoria.registrar(db, usuario.email, "servicio", servicio.id, "UPDATE", f"Actualizó servicio '{servicio.nombre}'")
    return servicio


@router.delete("/servicios/{servicio_id}")
def desactivar_servicio(
    servicio_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    servicio = crud.servicios.obtener(db, servicio_id)
    if not servicio:
        raise HTTPException(404, "Servicio no encontrado")
    dep = crud.dependencias.obtener(db, servicio.dependencia_id)
    if not security.puede_editar_area(usuario, dep.area):
        raise HTTPException(403, "No tienes permiso para editar este servicio")

    crud.servicios.desactivar(db, servicio)
    crud.auditoria.registrar(db, usuario.email, "servicio", servicio.id, "DELETE", f"Desactivó servicio '{servicio.nombre}'")
    return {"ok": True}
