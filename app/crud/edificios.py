from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas


def listar(db: Session, sede_id: Optional[int] = None) -> list[models.Edificio]:
    q = db.query(models.Edificio).filter(models.Edificio.estado == "activo")
    if sede_id is not None:
        q = q.filter(models.Edificio.sede_id == sede_id)
    return q.order_by(models.Edificio.nombre).all()


def obtener(db: Session, edificio_id: int) -> Optional[models.Edificio]:
    return db.query(models.Edificio).filter(models.Edificio.id == edificio_id).first()


def crear(db: Session, data: schemas.EdificioCreate) -> models.Edificio:
    edificio = models.Edificio(**data.model_dump())
    db.add(edificio)
    db.commit()
    db.refresh(edificio)
    return edificio


def actualizar(db: Session, edificio: models.Edificio, data: schemas.EdificioUpdate) -> models.Edificio:
    for k, v in data.model_dump().items():
        setattr(edificio, k, v)
    db.commit()
    db.refresh(edificio)
    return edificio
