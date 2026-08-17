from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app import crud, models, schemas, security
from app.database import get_db

router = APIRouter()


def _puede_editar(usuario: models.Usuario, dependencia: models.Dependencia) -> bool:
    if usuario.rol == "admin":
        return True
    return bool(usuario.area) and usuario.area == dependencia.area


@router.get("/dependencias", response_model=list[schemas.DependenciaOut])
def listar_dependencias(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(security.get_usuario_actual),
):
    q = db.query(models.Dependencia).options(joinedload(models.Dependencia.alias))
    if usuario.rol != "admin":
        q = q.filter(models.Dependencia.area == usuario.area)
    deps = q.order_by(models.Dependencia.nombre).all()
    return [schemas.DependenciaOut(**crud.dependencia_a_out(d)) for d in deps]


@router.post("/dependencias", response_model=schemas.DependenciaOut)
def crear_dependencia(
    payload: schemas.DependenciaCreate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(security.get_usuario_actual),
):
    if usuario.rol != "admin" and payload.area != usuario.area:
        raise HTTPException(403, "Solo puedes crear dependencias dentro de tu propia área")

    data = payload.model_dump(exclude={"alias"})
    dep = crud.crear_dependencia(db, data, payload.alias)
    crud.registrar_auditoria(db, usuario.email, dep.id, "CREATE", f"Creó '{dep.nombre}'")
    return schemas.DependenciaOut(**crud.dependencia_a_out(dep))


@router.put("/dependencias/{dep_id}", response_model=schemas.DependenciaOut)
def actualizar_dependencia(
    dep_id: int,
    payload: schemas.DependenciaUpdate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(security.get_usuario_actual),
):
    dep = db.query(models.Dependencia).filter(models.Dependencia.id == dep_id).first()
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not _puede_editar(usuario, dep):
        raise HTTPException(403, "No tienes permiso para editar esta dependencia")

    cambios = []
    data = payload.model_dump(exclude={"alias"})
    for k, v in data.items():
        if getattr(dep, k) != v:
            cambios.append(f"{k}: '{getattr(dep, k)}' -> '{v}'")

    dep = crud.actualizar_dependencia(db, dep, data, payload.alias)
    crud.registrar_auditoria(
        db, usuario.email, dep.id, "UPDATE", "; ".join(cambios) or "Sin cambios detectados"
    )
    return schemas.DependenciaOut(**crud.dependencia_a_out(dep))


@router.delete("/dependencias/{dep_id}")
def desactivar_dependencia(
    dep_id: int,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(security.get_usuario_actual),
):
    dep = db.query(models.Dependencia).filter(models.Dependencia.id == dep_id).first()
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not _puede_editar(usuario, dep):
        raise HTTPException(403, "No tienes permiso para modificar esta dependencia")

    dep.estado = "inactivo"
    db.commit()
    crud.registrar_auditoria(db, usuario.email, dep.id, "DELETE", f"Desactivó '{dep.nombre}'")
    return {"ok": True}


@router.get("/auditoria", response_model=list[schemas.AuditoriaOut])
def ver_auditoria(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(security.requiere_admin),
    limite: int = 100,
):
    return (
        db.query(models.Auditoria)
        .order_by(models.Auditoria.fecha.desc())
        .limit(limite)
        .all()
    )


@router.get("/metricas/resumen")
def resumen_metricas(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(security.get_usuario_actual),
):
    total = db.query(func.count(models.ConsultaLog.id)).scalar() or 0
    encontradas = (
        db.query(func.count(models.ConsultaLog.id))
        .filter(models.ConsultaLog.encontrado.is_(True))
        .scalar()
        or 0
    )
    sin_resultado = total - encontradas
    top = (
        db.query(models.ConsultaLog.query_text, func.count(models.ConsultaLog.id).label("n"))
        .group_by(models.ConsultaLog.query_text)
        .order_by(func.count(models.ConsultaLog.id).desc())
        .limit(10)
        .all()
    )
    return {
        "total_consultas": total,
        "consultas_resueltas": encontradas,
        "consultas_sin_resultado": sin_resultado,
        "porcentaje_resueltas": round((encontradas / total) * 100, 1) if total else None,
        "top_consultas": [{"consulta": t, "veces": n} for t, n in top],
    }
