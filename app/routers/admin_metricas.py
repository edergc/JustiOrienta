from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, security
from app.database import get_db

router = APIRouter()


@router.get("/resumen")
def resumen_metricas(
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    total = db.query(func.count(models.ConsultaLog.id)).scalar() or 0
    encontradas = (
        db.query(func.count(models.ConsultaLog.id))
        .filter(models.ConsultaLog.encontrado.is_(True))
        .scalar()
        or 0
    )
    sin_resultado = total - encontradas

    con_respuesta = (
        db.query(func.count(models.ConsultaLog.id))
        .filter(models.ConsultaLog.satisfaccion.isnot(None))
        .scalar()
        or 0
    )
    satisfechas = (
        db.query(func.count(models.ConsultaLog.id))
        .filter(models.ConsultaLog.satisfaccion == "si")
        .scalar()
        or 0
    )

    top = (
        db.query(models.ConsultaLog.query_text, func.count(models.ConsultaLog.id).label("n"))
        .group_by(models.ConsultaLog.query_text)
        .order_by(func.count(models.ConsultaLog.id).desc())
        .limit(10)
        .all()
    )

    def _porcentaje(filtro):
        n = db.query(func.count(models.ConsultaLog.id)).filter(filtro).scalar() or 0
        return round((n / total) * 100, 1) if total else None

    por_sede = (
        db.query(models.Sede.nombre, func.count(models.ConsultaLog.id).label("n"))
        .join(models.ConsultaLog, models.ConsultaLog.sede_contexto_id == models.Sede.id)
        .group_by(models.Sede.nombre)
        .order_by(func.count(models.ConsultaLog.id).desc())
        .all()
    )

    return {
        "total_consultas": total,
        "consultas_resueltas": encontradas,
        "consultas_sin_resultado": sin_resultado,
        "porcentaje_resueltas": round((encontradas / total) * 100, 1) if total else None,
        "respuestas_satisfaccion": con_respuesta,
        "porcentaje_satisfaccion": round((satisfechas / con_respuesta) * 100, 1) if con_respuesta else None,
        "top_consultas": [{"consulta": t, "veces": n} for t, n in top],
        # ── Indicadores de uso y accesibilidad (sección 30) ──
        "porcentaje_modo_accesible": _porcentaje(models.ConsultaLog.modo_accesible.is_(True)),
        "porcentaje_via_voz": _porcentaje(models.ConsultaLog.via_voz.is_(True)),
        "porcentaje_sobre_accesibilidad": _porcentaje(models.ConsultaLog.sobre_accesibilidad.is_(True)),
        "consultas_por_sede": [{"sede": s, "veces": n} for s, n in por_sede],
    }
