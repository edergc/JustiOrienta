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
