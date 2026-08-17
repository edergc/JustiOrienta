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
    crud.busqueda.registrar_consulta(db, q, encontrado)

    if not encontrado:
        return schemas.BusquedaRespuesta(
            resultados=[],
            total=0,
            fallback=True,
            mensaje=(
                "No podemos identificar con seguridad lo que buscas. "
                "Acércate al módulo de orientación o escribe al canal institucional de atención."
            ),
        )

    salida = [schemas.DependenciaOut.model_validate(d) for d in resultados]
    return schemas.BusquedaRespuesta(resultados=salida, total=len(salida), fallback=False)


@router.get("/dependencias/{dep_id}", response_model=schemas.DependenciaOut)
def obtener_dependencia(dep_id: int, db: Session = Depends(get_db)):
    dep = crud.dependencias.obtener_activa(db, dep_id)
    if not dep:
        raise HTTPException(status_code=404, detail="Dependencia no encontrada o no publicada")
    return schemas.DependenciaOut.model_validate(dep)


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
