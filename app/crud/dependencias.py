from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app import models, schemas


def _cargar(q):
    return q.options(
        joinedload(models.Dependencia.alias),
        joinedload(models.Dependencia.sede),
        joinedload(models.Dependencia.edificio),
        joinedload(models.Dependencia.servicios_detalle),
    )


def listar(
    db: Session,
    area: Optional[str] = None,
    estado: Optional[str] = None,
    skip: int = 0,
    limite: int = 50,
) -> list[models.Dependencia]:
    q = _cargar(db.query(models.Dependencia))
    if area is not None:
        q = q.filter(models.Dependencia.area == area)
    if estado is not None:
        q = q.filter(models.Dependencia.estado == estado)
    return q.order_by(models.Dependencia.nombre).offset(skip).limit(limite).all()


def contar(db: Session, area: Optional[str] = None, estado: Optional[str] = None) -> int:
    q = db.query(models.Dependencia)
    if area is not None:
        q = q.filter(models.Dependencia.area == area)
    if estado is not None:
        q = q.filter(models.Dependencia.estado == estado)
    return q.count()


def obtener(db: Session, dep_id: int) -> Optional[models.Dependencia]:
    return _cargar(db.query(models.Dependencia)).filter(models.Dependencia.id == dep_id).first()


def obtener_activa(db: Session, dep_id: int) -> Optional[models.Dependencia]:
    return _cargar(db.query(models.Dependencia)).filter(
        models.Dependencia.id == dep_id, models.Dependencia.estado == "activo"
    ).first()


def _sincronizar_alias(db: Session, dependencia: models.Dependencia, alias_csv: str) -> None:
    nuevos = [a.strip() for a in (alias_csv or "").split(",") if a.strip()]
    dependencia.alias.clear()
    db.flush()
    for a in nuevos:
        dependencia.alias.append(models.Alias(alias=a))


def crear(db: Session, data: dict, alias_csv: str) -> models.Dependencia:
    dep = models.Dependencia(**data)
    db.add(dep)
    db.flush()
    _sincronizar_alias(db, dep, alias_csv)
    db.commit()
    db.refresh(dep)
    return obtener(db, dep.id)


def actualizar(
    db: Session, dep: models.Dependencia, data: dict, alias_csv: Optional[str]
) -> models.Dependencia:
    for k, v in data.items():
        setattr(dep, k, v)
    if alias_csv is not None:
        _sincronizar_alias(db, dep, alias_csv)
    db.commit()
    db.refresh(dep)
    return obtener(db, dep.id)


def aprobar(db: Session, dep: models.Dependencia) -> models.Dependencia:
    dep.estado = "activo"
    db.commit()
    db.refresh(dep)
    return obtener(db, dep.id)


def enviar_a_revision(db: Session, dep: models.Dependencia) -> models.Dependencia:
    dep.estado = "revision"
    db.commit()
    db.refresh(dep)
    return obtener(db, dep.id)


def desactivar(db: Session, dep: models.Dependencia) -> None:
    dep.estado = "inactivo"
    db.commit()
