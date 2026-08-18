"""Detector de posibles duplicados en el catálogo.

Encuentra sistemáticamente casos como el ya documentado en el README ("De
dónde salen los datos reales"): el directorio oficial repite nombres
genéricos como "Mesa de Partes" para oficinas DISTINTAS dentro de la misma
sede (Bienestar Social, Control de Asistencia, Escalafón...). Esos ya se
corrigieron a mano una vez -- este detector es para no depender de que
alguien lo note de nuevo revisando cientos de filas.

Deliberadamente solo agrupa por nombre normalizado IDÉNTICO dentro de la
misma sede -- nada de "similar pero no igual" (distancia de edición): en
este catálogo eso generaría falsos positivos graves, porque los juzgados se
distinguen justo por un número ("10.º Juzgado Civil" vs "11.º Juzgado
Civil" son oficinas legítimamente distintas que solo difieren en un
carácter). Preferible un detector preciso y confiable a uno ruidoso que la
gente termine ignorando.
"""
from collections import defaultdict

from sqlalchemy.orm import Session, joinedload

from app import models
from app.models import normalizar


def _resumen(dep: models.Dependencia) -> dict:
    return {
        "id": dep.id,
        "nombre": dep.nombre,
        "area": dep.area or "Sin área",
        "estado": dep.estado,
        "piso": dep.piso,
        "oficina": dep.oficina,
    }


def detectar_duplicados(db: Session) -> list[dict]:
    """Un grupo por cada (sede, nombre normalizado) con más de una
    dependencia -- lo inactivo se excluye porque ya está descartado, no vale
    la pena revisarlo de nuevo."""
    deps = (
        db.query(models.Dependencia)
        .options(joinedload(models.Dependencia.sede))
        .filter(models.Dependencia.estado != "inactivo")
        .all()
    )

    por_clave: dict[tuple, list[models.Dependencia]] = defaultdict(list)
    for dep in deps:
        nombre_norm = dep.nombre_normalizado or normalizar(dep.nombre)
        por_clave[(dep.sede_id, nombre_norm)].append(dep)

    grupos = [
        {
            "sede": candidatas[0].sede.nombre if candidatas[0].sede else "Sede no registrada",
            "nombre": candidatas[0].nombre,
            "dependencias": [_resumen(d) for d in candidatas],
        }
        for candidatas in por_clave.values()
        if len(candidatas) > 1
    ]
    grupos.sort(key=lambda g: (-len(g["dependencias"]), g["sede"], g["nombre"]))
    return grupos
