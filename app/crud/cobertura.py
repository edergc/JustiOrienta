from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas


def listar(db: Session, estado: Optional[str] = None) -> list[models.SolicitudCobertura]:
    q = db.query(models.SolicitudCobertura)
    if estado:
        q = q.filter(models.SolicitudCobertura.estado == estado)
    return q.order_by(models.SolicitudCobertura.creado_en.desc()).all()


def obtener(db: Session, solicitud_id: int) -> Optional[models.SolicitudCobertura]:
    return db.query(models.SolicitudCobertura).filter(models.SolicitudCobertura.id == solicitud_id).first()


def crear(db: Session, payload: schemas.SolicitudCoberturaCreate, creado_por: str) -> models.SolicitudCobertura:
    s = models.SolicitudCobertura(
        query_text=payload.query_text,
        area=payload.area,
        comentario=payload.comentario,
        creado_por=creado_por,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def actualizar(
    db: Session, solicitud: models.SolicitudCobertura, payload: schemas.SolicitudCoberturaUpdate
) -> models.SolicitudCobertura:
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(solicitud, k, v)
    db.commit()
    db.refresh(solicitud)
    return solicitud
