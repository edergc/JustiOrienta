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
    top = (
        db.query(models.ConsultaLog.query_text, func.count(models.ConsultaLog.id).label("n"))
        .group_by(models.ConsultaLog.query_text)
        .order_by(func.count(models.ConsultaLog.id).desc())
        .limit(10)
        .all()
    )
    return {
        "total_consultas": total,
        "consultas_resueltas": encontradas,
        "consultas_sin_resultado": sin_resultado,
        "porcentaje_resueltas": round((encontradas / total) * 100, 1) if total else None,
        "top_consultas": [{"consulta": t, "veces": n} for t, n in top],
    }
