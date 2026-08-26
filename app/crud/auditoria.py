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
) -> None:
    db.add(
        models.Auditoria(
            usuario_dni=usuario_dni,
            entidad=entidad,
            entidad_id=entidad_id,
            accion=accion,
            detalle=detalle,
        )
    )
    db.commit()


def listar(db: Session, limite: int = 100) -> list[models.Auditoria]:
    return (
        db.query(models.Auditoria)
        .order_by(models.Auditoria.fecha.desc())
        .limit(limite)
        .all()
    )


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
