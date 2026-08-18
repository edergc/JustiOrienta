import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, security
from app.config import settings
from app.database import get_db
from app.models.base import ahora_utc

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
    # "consultas por área" y "consultas por tipo" -- indicadores de uso que
    # pide explícitamente la sección 30 del proyecto, junto con por-sede.
    por_area = (
        db.query(models.Dependencia.area, func.count(models.ConsultaLog.id).label("n"))
        .join(models.ConsultaLog, models.ConsultaLog.dependencia_resultado_id == models.Dependencia.id)
        .group_by(models.Dependencia.area)
        .order_by(func.count(models.ConsultaLog.id).desc())
        .all()
    )
    por_tipo = (
        db.query(models.Dependencia.tipo, func.count(models.ConsultaLog.id).label("n"))
        .join(models.ConsultaLog, models.ConsultaLog.dependencia_resultado_id == models.Dependencia.id)
        .group_by(models.Dependencia.tipo)
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
        "consultas_por_area": [{"area": a or "Sin área", "veces": n} for a, n in por_area],
        "consultas_por_tipo": [{"tipo": t, "veces": n} for t, n in por_tipo],
    }


def _hoja_tabla(wb: Workbook, titulo: str, encabezados: list[str], filas: list[tuple]):
    ws = wb.create_sheet(titulo)
    ws.append(encabezados)
    for celda in ws[1]:
        celda.font = Font(bold=True)
    for fila in filas:
        ws.append(fila)
    for col in ws.columns:
        ancho = max(len(str(c.value)) for c in col if c.value is not None) + 2
        ws.column_dimensions[col[0].column_letter].width = min(max(ancho, 12), 60)
    return ws


@router.get("/reporte.xlsx")
def descargar_reporte(
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_lectura_reportes),
):
    """Reporte descargable en Excel con la misma foto de indicadores que
    muestra el panel -- pensado para llevar a una reunión o adjuntar a un
    informe, sin depender de que quien lo necesita tenga acceso al sistema
    en ese momento."""
    datos = resumen_metricas(db=db, usuario=usuario)

    wb = Workbook()
    wb.remove(wb.active)

    resumen = wb.create_sheet("Resumen")
    resumen.append([settings.app_name, f"v{settings.app_version}"])
    resumen["A1"].font = Font(bold=True, size=14)
    resumen.append([f"Generado: {ahora_utc().strftime('%d/%m/%Y %H:%M')} UTC"])
    resumen.append([])
    filas_resumen = [
        ("Consultas totales", datos["total_consultas"]),
        ("Resueltas", datos["consultas_resueltas"]),
        ("Sin resultado", datos["consultas_sin_resultado"]),
        ("% de acierto", datos["porcentaje_resueltas"]),
        ("Respuestas de satisfacción", datos["respuestas_satisfaccion"]),
        ("% de satisfacción (de quienes respondieron)", datos["porcentaje_satisfaccion"]),
        ("% en modo accesible", datos["porcentaje_modo_accesible"]),
        ("% por voz", datos["porcentaje_via_voz"]),
        ("% sobre accesibilidad", datos["porcentaje_sobre_accesibilidad"]),
    ]
    resumen.append(["Indicador", "Valor"])
    for celda in resumen[4]:
        celda.font = Font(bold=True)
    for fila in filas_resumen:
        resumen.append(fila)
    resumen.column_dimensions["A"].width = 45
    resumen.column_dimensions["B"].width = 18

    _hoja_tabla(wb, "Consultas más frecuentes", ["Consulta", "Veces"],
                [(t["consulta"], t["veces"]) for t in datos["top_consultas"]])
    _hoja_tabla(wb, "Por sede", ["Sede", "Veces"],
                [(c["sede"], c["veces"]) for c in datos["consultas_por_sede"]])
    _hoja_tabla(wb, "Por área", ["Área", "Veces"],
                [(c["area"], c["veces"]) for c in datos["consultas_por_area"]])
    _hoja_tabla(wb, "Por tipo", ["Tipo", "Veces"],
                [(c["tipo"], c["veces"]) for c in datos["consultas_por_tipo"]])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    nombre_archivo = f"reporte_justicia_orienta_{ahora_utc().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )
