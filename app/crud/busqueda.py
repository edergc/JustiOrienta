from sqlalchemy.orm import Session, joinedload

from app import models, nlp
from app.models import normalizar


def _puntuar(nq: str, tokens: list[str], dep: models.Dependencia) -> float:
    score = 0.0
    nombre_norm = dep.nombre_normalizado or normalizar(dep.nombre)
    nombre_tokens = set(nombre_norm.split())
    alias_norm = [a.alias_normalizado or normalizar(a.alias) for a in dep.alias]
    alias_tokens = [set(a.split()) for a in alias_norm]

    if nombre_norm == nq:
        score += 10
    if nq in alias_norm:
        score += 10
    if any(nq in a or a in nq for a in alias_norm):
        score += 6
    if nq in nombre_norm:
        score += 5
    for tok in tokens:
        # Coincidencia de palabra completa, no de substring: si fuera "tok in
        # nombre_norm" a secas, buscar "5" encontraría falsos positivos
        # dentro de "15", "25", "35"... igual que "no" dentro de "informaNOs".
        if tok in nombre_tokens:
            score += 1
        if any(tok in a for a in alias_tokens):
            score += 1
        if dep.servicios and tok in normalizar(dep.servicios).split():
            score += 0.5
        for serv in dep.servicios_detalle:
            if serv.estado == "activo" and tok in normalizar(serv.nombre).split():
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


def _filtrar_por_numero(tokens: list[str], puntuadas: list[tuple[float, "models.Dependencia"]]):
    """Si la consulta trae un número ("11 juzgado civil"), es el dato más
    específico que puede dar una persona -- de nada sirve mostrar cinco
    juzgados civiles distintos si uno de ellos SÍ es el número exacto.
    Cuando al menos un resultado coincide con todos los números pedidos, se
    descartan los que no -- si ninguno coincide, se deja la lista tal cual en
    vez de vaciarla (mejor una respuesta aproximada que ninguna)."""
    numeros = [t for t in tokens if t.isdigit()]
    if not numeros:
        return puntuadas

    def coincide(dep):
        nombre_tokens = (dep.nombre_normalizado or "").split()
        alias_tokens = {t for a in dep.alias for t in (a.alias_normalizado or "").split()}
        return all(n in nombre_tokens or n in alias_tokens for n in numeros)

    con_numero = [(s, d) for s, d in puntuadas if coincide(d)]
    return con_numero if con_numero else puntuadas


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
    # Al menos 3 letras para evitar ruido de palabras cortas ("no", "de"),
    # pero los números se conservan siempre: "11", "23"... son justo el dato
    # más específico de un juzgado y antes se estaban descartando.
    tokens = [t for t in nq.split(" ") if len(t) >= 3 or t.isdigit()]

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
    puntuadas = _filtrar_por_numero(tokens, puntuadas)

    if not puntuadas:
        puntuadas = [(_puntuar_por_similitud(tokens, dep), dep) for dep in activas]
        puntuadas = [(s, d) for s, d in puntuadas if s > 0]

    puntuadas.sort(key=lambda x: x[0], reverse=True)
    return [dep for _, dep in puntuadas[:limite]]


def info_accesibilidad_sede(db: Session, sede_id: int) -> "models.Sede | None":
    """Responde directo desde los booleanos de la sede cuando la persona
    pregunta por accesibilidad en general (rampa, ascensor...) y ya se sabe
    en qué sede está, sin necesidad de nombrar una dependencia puntual."""
    return db.query(models.Sede).filter(models.Sede.id == sede_id).first()


def registrar_consulta(
    db: Session,
    query: str,
    encontrado: bool,
    sede_contexto_id: int | None = None,
    dependencia_resultado_id: int | None = None,
    modo_accesible: bool = False,
    via_voz: bool = False,
    sobre_accesibilidad: bool = False,
) -> models.ConsultaLog:
    log = models.ConsultaLog(
        query_text=query[:300],
        encontrado=encontrado,
        sede_contexto_id=sede_contexto_id,
        dependencia_resultado_id=dependencia_resultado_id,
        modo_accesible=modo_accesible,
        via_voz=via_voz,
        sobre_accesibilidad=sobre_accesibilidad,
    )
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
