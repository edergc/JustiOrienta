from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas


def listar_por_dependencia(db: Session, dependencia_id: int) -> list[models.Servicio]:
    return (
        db.query(models.Servicio)
        .filter(models.Servicio.dependencia_id == dependencia_id, models.Servicio.estado == "activo")
        .order_by(models.Servicio.nombre)
        .all()
    )


def obtener(db: Session, servicio_id: int) -> Optional[models.Servicio]:
    return db.query(models.Servicio).filter(models.Servicio.id == servicio_id).first()


def crear(db: Session, dependencia_id: int, data: schemas.ServicioCreate) -> models.Servicio:
    servicio = models.Servicio(dependencia_id=dependencia_id, **data.model_dump())
    db.add(servicio)
    db.commit()
    db.refresh(servicio)
    return servicio


def actualizar(db: Session, servicio: models.Servicio, data: schemas.ServicioUpdate) -> models.Servicio:
    for k, v in data.model_dump().items():
        setattr(servicio, k, v)
    db.commit()
    db.refresh(servicio)
    return servicio


def desactivar(db: Session, servicio: models.Servicio) -> None:
    servicio.estado = "inactivo"
    db.commit()
