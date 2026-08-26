from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, nlp, schemas
from app.config import settings
from app.database import get_db
from app.reportes_pdf import generar_directorio_pdf

router = APIRouter()


@router.get("/buscar", response_model=schemas.BusquedaRespuesta)
def buscar(
    q: str = Query("", min_length=0),
    sede_contexto: Optional[int] = Query(None, description="Id de sede conocida por ?sede= en la URL"),
    modo_accesible: bool = Query(False, description="Alto contraste, texto ampliado o tema oscuro activos"),
    via_voz: bool = Query(False, description="La consulta llegó por reconocimiento de voz"),
    db: Session = Depends(get_db),
):
    if not q.strip():
        return schemas.BusquedaRespuesta(resultados=[], total=0, fallback=False)

    nq = nlp.interpretar(q)
    sobre_accesibilidad = nlp.es_pregunta_de_accesibilidad(nq)

    sede_accesibilidad = None
    if sobre_accesibilidad and sede_contexto:
        sede_accesibilidad = crud.busqueda.info_accesibilidad_sede(db, sede_contexto)
    sede_out = schemas.SedeOut.model_validate(sede_accesibilidad) if sede_accesibilidad else None

    resultados = crud.busqueda.buscar_dependencias(db, q)
    encontrado = len(resultados) > 0
    dependencia_resultado_id = resultados[0].id if encontrado else None

    consulta = crud.busqueda.registrar_consulta(
        db,
        q,
        encontrado,
        sede_contexto_id=sede_contexto,
        dependencia_resultado_id=dependencia_resultado_id,
        modo_accesible=modo_accesible,
        via_voz=via_voz,
        sobre_accesibilidad=sobre_accesibilidad,
    )

    if not encontrado:
        return schemas.BusquedaRespuesta(
            resultados=[],
            total=0,
            # Si pudimos responder la accesibilidad directo desde la sede, no
            # es realmente un callejón sin salida aunque no haya dependencias.
            fallback=sede_out is None,
            consulta_id=consulta.id,
            sede_accesibilidad=sede_out,
            mensaje=(
                None
                if sede_out
                else "No podemos identificar con seguridad lo que buscas. "
                "Acércate al módulo de orientación o escribe al canal institucional de atención."
            ),
        )

    salida = [schemas.DependenciaOut.model_validate(d) for d in resultados]
    return schemas.BusquedaRespuesta(
        resultados=salida,
        total=len(salida),
        fallback=False,
        consulta_id=consulta.id,
        sede_accesibilidad=sede_out,
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


@router.get("/sedes/{sede_id}/dependencias", response_model=list[schemas.DependenciaOut])
def dependencias_de_sede(sede_id: int, db: Session = Depends(get_db)):
    """"Estoy aquí": todas las dependencias publicadas de una sede en una sola
    vista, para quien ya sabe en qué sede está y solo quiere ver qué hay --
    sin necesidad de escribir o hablar una búsqueda. Reutiliza exactamente el
    mismo filtro (solo estado='activo') que ya usa el directorio en PDF."""
    sede = crud.sedes.obtener(db, sede_id)
    if not sede:
        raise HTTPException(404, "La sede indicada no existe")
    deps = crud.dependencias.listar_activas(db, sede_id=sede_id)
    return [schemas.DependenciaOut.model_validate(d) for d in deps]


@router.get("/directorio.pdf")
def directorio_pdf(
    sede_id: Optional[int] = Query(None, description="Limita el directorio a una sola sede"),
    db: Session = Depends(get_db),
):
    """Directorio público imprimible -- para pegar en un mostrador o llevarse
    sin conexión, sin depender de que el sitio con JavaScript esté disponible
    en ese momento. Solo incluye lo publicado (estado='activo'), igual que la
    búsqueda pública; nunca contenido en revisión."""
    sede_nombre = None
    if sede_id is not None:
        sede = crud.sedes.obtener(db, sede_id)
        if not sede:
            raise HTTPException(404, "La sede indicada no existe")
        sede_nombre = sede.nombre

    deps = crud.dependencias.listar_activas(db, sede_id=sede_id)
    pdf_bytes = generar_directorio_pdf(deps, sede_nombre)
    nombre_archivo = f"directorio_justicia_orienta_{datetime.now().strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        # inline (no "attachment"): abre en el visor de PDF del navegador,
        # desde donde imprimir es un clic -- igual que el botón "QR" del panel
        # abre una pestaña nueva en vez de forzar la descarga.
        headers={"Content-Disposition": f'inline; filename="{nombre_archivo}"'},
    )


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
