from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas


def listar(db: Session, incluir_inactivas: bool = False) -> list[models.Sede]:
    q = db.query(models.Sede)
    if not incluir_inactivas:
        q = q.filter(models.Sede.estado == "activo")
    return q.order_by(models.Sede.nombre).all()


def obtener(db: Session, sede_id: int) -> Optional[models.Sede]:
    return db.query(models.Sede).filter(models.Sede.id == sede_id).first()


def crear(db: Session, data: schemas.SedeCreate) -> models.Sede:
    sede = models.Sede(**data.model_dump())
    db.add(sede)
    db.commit()
    db.refresh(sede)
    return sede


def actualizar(db: Session, sede: models.Sede, data: schemas.SedeUpdate) -> models.Sede:
    for k, v in data.model_dump().items():
        setattr(sede, k, v)
    db.commit()
    db.refresh(sede)
    return sede
