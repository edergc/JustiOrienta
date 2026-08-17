from sqlalchemy.orm import Session, joinedload

from app import models, nlp
from app.models import normalizar


def _puntuar(nq: str, tokens: list[str], dep: models.Dependencia) -> float:
    score = 0.0
    nombre_norm = dep.nombre_normalizado or normalizar(dep.nombre)
    alias_norm = [a.alias_normalizado or normalizar(a.alias) for a in dep.alias]

    if nombre_norm == nq:
        score += 10
    if nq in alias_norm:
        score += 10
    if any(nq in a or a in nq for a in alias_norm):
        score += 6
    if nq in nombre_norm:
        score += 5
    for tok in tokens:
        if tok in nombre_norm:
            score += 1
        if any(tok in a for a in alias_norm):
            score += 1
        if dep.servicios and tok in normalizar(dep.servicios):
            score += 0.5
        for serv in dep.servicios_detalle:
            if serv.estado == "activo" and tok in normalizar(serv.nombre):
                score += 0.5
    return score


def _puntuar_por_similitud(tokens: list[str], dep: models.Dependencia) -> float:
    """Respaldo para errores de tipeo: solo se usa cuando la búsqueda exacta
    no encontró nada, para no opacar coincidencias reales con adivinanzas."""
    nombre_norm = dep.nombre_normalizado or normalizar(dep.nombre)
    alias_norm = [a.alias_normalizado or normalizar(a.alias) for a in dep.alias]
    vocabulario = set(nombre_norm.split())
    for a in alias_norm:
        vocabulario.update(a.split())

    score = 0.0
    for tok in tokens:
        if len(tok) < 4:
            continue
        if any(nlp.es_similar(tok, palabra) for palabra in vocabulario):
            score += 2
    return score


def buscar_dependencias(db: Session, query: str, limite: int = 10) -> list[models.Dependencia]:
    """Búsqueda en lenguaje natural, en Python -- portable entre SQLite y
    PostgreSQL sin depender de extensiones como pg_trgm.

    Entiende: mayúsculas/tildes, frases de cortesía ("¿me podría decir
    dónde queda...?"), números escritos en palabras ("once" == "11",
    "treinta y dos" == "32", "onceavo" == "11") y tolera errores de tipeo
    menores como respaldo cuando no hay coincidencia exacta.
    """
    nq = nlp.interpretar(query)
    if not nq:
        return []
    tokens = [t for t in nq.split(" ") if len(t) >= 3]

    activas = (
        db.query(models.Dependencia)
        .options(
            joinedload(models.Dependencia.alias),
            joinedload(models.Dependencia.sede),
            joinedload(models.Dependencia.edificio),
            joinedload(models.Dependencia.servicios_detalle),
        )
        .filter(models.Dependencia.estado == "activo")
        .all()
    )

    puntuadas = [(_puntuar(nq, tokens, dep), dep) for dep in activas]
    puntuadas = [(s, d) for s, d in puntuadas if s > 0]

    if not puntuadas:
        puntuadas = [(_puntuar_por_similitud(tokens, dep), dep) for dep in activas]
        puntuadas = [(s, d) for s, d in puntuadas if s > 0]

    puntuadas.sort(key=lambda x: x[0], reverse=True)
    return [dep for _, dep in puntuadas[:limite]]


def registrar_consulta(db: Session, query: str, encontrado: bool) -> models.ConsultaLog:
    log = models.ConsultaLog(query_text=query[:300], encontrado=encontrado)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


VALORES_SATISFACCION = {"si", "parcial", "no"}


def registrar_satisfaccion(db: Session, consulta_id: int, valor: str) -> bool:
    """Devuelve False si la consulta no existe o el valor no es válido --
    la respuesta anónima no debe poder inventar registros nuevos."""
    if valor not in VALORES_SATISFACCION:
        return False
    log = db.query(models.ConsultaLog).filter(models.ConsultaLog.id == consulta_id).first()
    if not log:
        return False
    log.satisfaccion = valor
    db.commit()
    return True
