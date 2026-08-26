from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.rutas_internas import construir_grafo, instrucciones_de_ruta, ruta_mas_corta


def listar_nodos(db: Session, sede_id: int, piso: Optional[str] = None) -> list[models.NodoUbicacion]:
    q = db.query(models.NodoUbicacion).filter(models.NodoUbicacion.sede_id == sede_id)
    if piso:
        q = q.filter(models.NodoUbicacion.piso == piso)
    return q.order_by(models.NodoUbicacion.piso, models.NodoUbicacion.nombre).all()


def obtener_nodo(db: Session, nodo_id: int) -> Optional[models.NodoUbicacion]:
    return db.query(models.NodoUbicacion).filter(models.NodoUbicacion.id == nodo_id).first()


def nodo_de_dependencia(db: Session, dependencia_id: int) -> Optional[models.NodoUbicacion]:
    return (
        db.query(models.NodoUbicacion)
        .filter(models.NodoUbicacion.dependencia_id == dependencia_id)
        .first()
    )


def crear_nodo(db: Session, payload: schemas.NodoCreate) -> models.NodoUbicacion:
    nodo = models.NodoUbicacion(**payload.model_dump())
    db.add(nodo)
    db.commit()
    db.refresh(nodo)
    return nodo


def actualizar_nodo(db: Session, nodo: models.NodoUbicacion, payload: schemas.NodoUpdate) -> models.NodoUbicacion:
    for k, v in payload.model_dump().items():
        setattr(nodo, k, v)
    db.commit()
    db.refresh(nodo)
    return nodo


def eliminar_nodo(db: Session, nodo: models.NodoUbicacion) -> None:
    # Sin esto, borrar un nodo con conexiones deja filas huérfanas en
    # conexiones_nodo apuntando a un id que ya no existe -- silenciosas
    # hasta que alguien intenta calcular una ruta que las cruza.
    db.query(models.ConexionNodo).filter(
        (models.ConexionNodo.nodo_a_id == nodo.id) | (models.ConexionNodo.nodo_b_id == nodo.id)
    ).delete(synchronize_session=False)
    db.delete(nodo)
    db.commit()


def listar_conexiones(db: Session, sede_id: int) -> list[models.ConexionNodo]:
    # No hay sede_id directo en conexiones_nodo -- se filtra por la sede del
    # nodo_a, que alcanza porque una conexión solo tiene sentido entre dos
    # nodos de la misma sede (nadie camina de un edificio a otro por un
    # pasillo interno).
    ids_nodos_sede = [n.id for n in db.query(models.NodoUbicacion.id).filter(models.NodoUbicacion.sede_id == sede_id)]
    return (
        db.query(models.ConexionNodo)
        .filter(models.ConexionNodo.nodo_a_id.in_(ids_nodos_sede))
        .all()
    )


def obtener_conexion(db: Session, conexion_id: int) -> Optional[models.ConexionNodo]:
    return db.query(models.ConexionNodo).filter(models.ConexionNodo.id == conexion_id).first()


def crear_conexion(db: Session, payload: schemas.ConexionCreate) -> models.ConexionNodo:
    conexion = models.ConexionNodo(**payload.model_dump())
    db.add(conexion)
    db.commit()
    db.refresh(conexion)
    return conexion


def actualizar_conexion(
    db: Session, conexion: models.ConexionNodo, payload: schemas.ConexionUpdate
) -> models.ConexionNodo:
    for k, v in payload.model_dump().items():
        setattr(conexion, k, v)
    db.commit()
    db.refresh(conexion)
    return conexion


def eliminar_conexion(db: Session, conexion: models.ConexionNodo) -> None:
    db.delete(conexion)
    db.commit()


def calcular_ruta(db: Session, origen_id: int, destino_dependencia_id: int) -> Optional[schemas.RutaOut]:
    """None si el origen no existe, si la dependencia no tiene un nodo
    asociado todavia, o si no hay un camino conectado entre ambos -- los
    tres casos se tratan igual (todavia no se puede armar la ruta), quien
    llama decide como comunicarlo."""
    origen = obtener_nodo(db, origen_id)
    if not origen:
        return None
    destino = nodo_de_dependencia(db, destino_dependencia_id)
    if not destino:
        return None

    conexiones = listar_conexiones(db, origen.sede_id)
    grafo = construir_grafo(conexiones)
    camino = ruta_mas_corta(grafo, origen.id, destino.id)
    if camino is None:
        return None

    pasos_grafo = instrucciones_de_ruta(grafo, camino)
    nodos_por_id = {
        n.id: n
        for n in db.query(models.NodoUbicacion).filter(models.NodoUbicacion.id.in_(camino))
    }

    pasos = [schemas.PasoRuta(nodo_id=camino[0], nombre=nodos_por_id[camino[0]].nombre, instruccion=None)]
    for paso in pasos_grafo:
        nodo = nodos_por_id[paso["hasta_id"]]
        pasos.append(schemas.PasoRuta(nodo_id=nodo.id, nombre=nodo.nombre, instruccion=paso["instruccion"]))

    return schemas.RutaOut(
        origen_id=origen.id,
        destino_id=destino.id,
        dependencia_nombre=destino.dependencia.nombre if destino.dependencia else destino.nombre,
        pasos=pasos,
    )
