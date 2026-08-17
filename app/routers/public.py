from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, schemas
from app.config import settings
from app.database import get_db

router = APIRouter()


@router.get("/buscar", response_model=schemas.BusquedaRespuesta)
def buscar(q: str = Query("", min_length=0), db: Session = Depends(get_db)):
    if not q.strip():
        return schemas.BusquedaRespuesta(resultados=[], total=0, fallback=False)

    resultados = crud.busqueda.buscar_dependencias(db, q)
    encontrado = len(resultados) > 0
    consulta = crud.busqueda.registrar_consulta(db, q, encontrado)

    if not encontrado:
        return schemas.BusquedaRespuesta(
            resultados=[],
            total=0,
            fallback=True,
            consulta_id=consulta.id,
            mensaje=(
                "No podemos identificar con seguridad lo que buscas. "
                "Acércate al módulo de orientación o escribe al canal institucional de atención."
            ),
        )

    salida = [schemas.DependenciaOut.model_validate(d) for d in resultados]
    return schemas.BusquedaRespuesta(
        resultados=salida, total=len(salida), fallback=False, consulta_id=consulta.id
    )


@router.post("/satisfaccion/{consulta_id}")
def registrar_satisfaccion(consulta_id: int, payload: schemas.SatisfaccionIn, db: Session = Depends(get_db)):
    ok = crud.busqueda.registrar_satisfaccion(db, consulta_id, payload.valor)
    if not ok:
        raise HTTPException(status_code=404, detail="No se pudo registrar: consulta o valor inválido")
    return {"ok": True}


@router.get("/dependencias/{dep_id}", response_model=schemas.DependenciaOut)
def obtener_dependencia(dep_id: int, db: Session = Depends(get_db)):
    dep = crud.dependencias.obtener_activa(db, dep_id)
    if not dep:
        raise HTTPException(status_code=404, detail="Dependencia no encontrada o no publicada")
    return schemas.DependenciaOut.model_validate(dep)


@router.get("/sedes", response_model=list[schemas.SedeOut])
def listar_sedes_publico(db: Session = Depends(get_db)):
    """Listado público de sedes -- lo usa el saludo contextual cuando alguien
    llega desde un QR de una sede específica (?sede=<id>)."""
    return crud.sedes.listar(db, incluir_inactivas=False)


@router.get("/salud")
def salud(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "proyecto": settings.app_name,
        "version": settings.app_version,
        "entorno": settings.entorno,
        "estado": "operativo" if db_ok else "degradado",
        "base_de_datos": "conectada" if db_ok else "sin conexión",
    }
