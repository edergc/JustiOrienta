from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app import crud, models, schemas
from app.database import get_db

router = APIRouter()


@router.get("/buscar", response_model=schemas.BusquedaRespuesta)
def buscar(q: str = Query("", min_length=0), db: Session = Depends(get_db)):
    if not q.strip():
        return schemas.BusquedaRespuesta(resultados=[], total=0, fallback=False)

    resultados = crud.buscar_dependencias(db, q)
    encontrado = len(resultados) > 0
    crud.registrar_consulta(db, q, encontrado)

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

    salida = [schemas.DependenciaOut(**crud.dependencia_a_out(d)) for d in resultados]
    return schemas.BusquedaRespuesta(resultados=salida, total=len(salida), fallback=False)


@router.get("/dependencias/{dep_id}", response_model=schemas.DependenciaOut)
def obtener_dependencia(dep_id: int, db: Session = Depends(get_db)):
    dep = (
        db.query(models.Dependencia)
        .options(joinedload(models.Dependencia.alias))
        .filter(models.Dependencia.id == dep_id, models.Dependencia.estado == "activo")
        .first()
    )
    if not dep:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Dependencia no encontrada o no publicada")
    return schemas.DependenciaOut(**crud.dependencia_a_out(dep))


@router.get("/salud")
def salud():
    return {"estado": "operativo", "proyecto": "Justicia Orienta"}
