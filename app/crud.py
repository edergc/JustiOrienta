from typing import Optional

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
    # Tokens de al menos 3 letras: evita falsos positivos por coincidencias de
    # substring con palabras cortas (p. ej. "no" dentro de "informaNOs").
    tokens = [t for t in nq.split(" ") if len(t) >= 3]

    activas = (
        db.query(models.Dependencia)
        .options(joinedload(models.Dependencia.alias))
        .filter(models.Dependencia.estado == "activo")
        .all()
    )

    puntuadas = [(_puntuar(nq, tokens, dep), dep) for dep in activas]
    puntuadas = [(s, d) for s, d in puntuadas if s > 0]

    if not puntuadas:
        # Respaldo por similitud: solo entra en juego si la búsqueda normal
        # no encontró nada, para tolerar errores de tipeo sin restar
        # precisión a las búsquedas que sí coinciden exactamente.
        puntuadas = [(_puntuar_por_similitud(tokens, dep), dep) for dep in activas]
        puntuadas = [(s, d) for s, d in puntuadas if s > 0]

    puntuadas.sort(key=lambda x: x[0], reverse=True)
    return [dep for _, dep in puntuadas[:limite]]


def registrar_consulta(db: Session, query: str, encontrado: bool) -> None:
    log = models.ConsultaLog(query_text=query[:300], encontrado=encontrado)
    db.add(log)
    db.commit()


def _sincronizar_alias(db: Session, dependencia: models.Dependencia, alias_csv: str) -> None:
    nuevos = [a.strip() for a in (alias_csv or "").split(",") if a.strip()]
    dependencia.alias.clear()
    db.flush()
    for a in nuevos:
        dependencia.alias.append(models.Alias(alias=a))


def crear_dependencia(db: Session, data: dict, alias_csv: str) -> models.Dependencia:
    dep = models.Dependencia(**data)
    db.add(dep)
    db.flush()
    _sincronizar_alias(db, dep, alias_csv)
    db.commit()
    db.refresh(dep)
    return dep


def actualizar_dependencia(
    db: Session, dep: models.Dependencia, data: dict, alias_csv: Optional[str]
) -> models.Dependencia:
    for k, v in data.items():
        setattr(dep, k, v)
    if alias_csv is not None:
        _sincronizar_alias(db, dep, alias_csv)
    db.commit()
    db.refresh(dep)
    return dep


def registrar_auditoria(
    db: Session, usuario_email: str, dependencia_id: Optional[int], accion: str, detalle: str
) -> None:
    db.add(
        models.Auditoria(
            usuario_email=usuario_email,
            dependencia_id=dependencia_id,
            accion=accion,
            detalle=detalle,
        )
    )
    db.commit()


def dependencia_a_out(dep: models.Dependencia) -> dict:
    d = {c.name: getattr(dep, c.name) for c in dep.__table__.columns}
    d["alias"] = [a.alias for a in dep.alias]
    return d
