from datetime import date, datetime, time
from typing import Optional

from sqlalchemy.orm import Session

from app import models


def registrar(
    db: Session,
    usuario_dni: str,
    entidad: str,
    entidad_id: Optional[int],
    accion: str,
    detalle: str,
    ip_origen: Optional[str] = None,
) -> None:
    db.add(
        models.Auditoria(
            usuario_dni=usuario_dni,
            entidad=entidad,
            entidad_id=entidad_id,
            accion=accion,
            detalle=detalle,
            ip_origen=ip_origen,
        )
    )
    db.commit()


def _filtrar(
    q,
    usuario_dni: Optional[str],
    entidad: Optional[str],
    accion: Optional[str],
    desde: Optional[date],
    hasta: Optional[date],
):
    if usuario_dni:
        q = q.filter(models.Auditoria.usuario_dni == usuario_dni)
    if entidad:
        q = q.filter(models.Auditoria.entidad == entidad)
    if accion:
        q = q.filter(models.Auditoria.accion == accion)
    if desde:
        q = q.filter(models.Auditoria.fecha >= datetime.combine(desde, time.min))
    if hasta:
        # hasta es un dia calendario completo (inclusive) -- sin esto,
        # "hasta = hoy" no traeria nada de lo registrado hoy mismo.
        q = q.filter(models.Auditoria.fecha <= datetime.combine(hasta, time.max))
    return q


def listar(
    db: Session,
    usuario_dni: Optional[str] = None,
    entidad: Optional[str] = None,
    accion: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    skip: int = 0,
    limite: int = 100,
) -> list[models.Auditoria]:
    q = _filtrar(db.query(models.Auditoria), usuario_dni, entidad, accion, desde, hasta)
    return q.order_by(models.Auditoria.fecha.desc()).offset(skip).limit(limite).all()


def contar(
    db: Session,
    usuario_dni: Optional[str] = None,
    entidad: Optional[str] = None,
    accion: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
) -> int:
    q = _filtrar(db.query(models.Auditoria), usuario_dni, entidad, accion, desde, hasta)
    return q.count()


def listar_por_entidad(db: Session, entidad: str, entidad_id: int, limite: int = 50) -> list[models.Auditoria]:
    """Historial de una sola dependencia/sede/etc. -- la mitad de la
    "trazabilidad de la orientacion" (Fase 4): quien publico este dato y
    cuando. La otra mitad (cuantas veces se mostro como respuesta) vive en
    ConsultaLog; se cruzan ambas en un solo endpoint, no aqui."""
    return (
        db.query(models.Auditoria)
        .filter(models.Auditoria.entidad == entidad, models.Auditoria.entidad_id == entidad_id)
        .order_by(models.Auditoria.fecha.desc())
        .limit(limite)
        .all()
    )
