from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas
from app.models.base import ahora_utc


def _generar_codigo(db: Session) -> str:
    """JO-2026-000145: año actual + un secuencial de 6 dígitos dentro de ese
    año. Se calcula contando lo que ya existe del año en vez de usar el id
    autoincremental de la tabla -- así el código no delata cuántas
    solicitudes de TODOS los tipos lleva el sistema, solo las de este año."""
    anio = ahora_utc().year
    prefijo = f"JO-{anio}-"
    cantidad = (
        db.query(models.SolicitudAtencion)
        .filter(models.SolicitudAtencion.codigo.like(f"{prefijo}%"))
        .count()
    )
    return f"{prefijo}{cantidad + 1:06d}"


def crear(db: Session, payload: schemas.SolicitudAtencionCreate) -> models.SolicitudAtencion:
    s = models.SolicitudAtencion(
        codigo=_generar_codigo(db),
        nombre_contacto=payload.nombre_contacto,
        telefono=payload.telefono,
        correo=payload.correo,
        motivo=payload.motivo,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def obtener_por_codigo(db: Session, codigo: str) -> Optional[models.SolicitudAtencion]:
    return db.query(models.SolicitudAtencion).filter(models.SolicitudAtencion.codigo == codigo.strip().upper()).first()


def obtener(db: Session, solicitud_id: int) -> Optional[models.SolicitudAtencion]:
    return db.query(models.SolicitudAtencion).filter(models.SolicitudAtencion.id == solicitud_id).first()


def listar(db: Session, estado: Optional[str] = None, area: Optional[str] = None) -> list[models.SolicitudAtencion]:
    q = db.query(models.SolicitudAtencion)
    if estado:
        q = q.filter(models.SolicitudAtencion.estado == estado)
    if area:
        q = q.filter(models.SolicitudAtencion.area == area)
    return q.order_by(models.SolicitudAtencion.creado_en.desc()).all()


def actualizar(
    db: Session, solicitud: models.SolicitudAtencion, payload: schemas.SolicitudAtencionUpdate
) -> models.SolicitudAtencion:
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(solicitud, k, v)
    db.commit()
    db.refresh(solicitud)
    return solicitud
