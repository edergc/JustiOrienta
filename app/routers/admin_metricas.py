import io
from collections import defaultdict

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, security
from app.config import settings
from app.database import get_db
from app.excel_utils import hoja_con_tabla
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
    # "consultas más frecuentes" mezcla encontradas y no encontradas -- para
    # decidir qué falta cargar en el catálogo, lo útil es aislar solo lo que
    # la gente busca y todavía NO encuentra (señal directa de demanda real).
    top_sin_resultado = (
        db.query(models.ConsultaLog.query_text, func.count(models.ConsultaLog.id).label("n"))
        .filter(models.ConsultaLog.encontrado.is_(False))
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

    # Antigüedad del contenido pendiente de aprobar, por área -- ayuda a ver
    # qué área no está validando a tiempo. Se agrega solo por área (cantidad +
    # promedio de días), sin nombrar dependencias puntuales: el rol "consulta"
    # ve este resumen y no debe terminar viendo contenido todavía no publicado
    # (la misma fuga que ya se cerró para GET /admin/dependencias).
    ahora = ahora_utc()
    pendientes = db.query(models.Dependencia).filter(models.Dependencia.estado == "revision").all()
    dias_por_area = defaultdict(list)
    for dep in pendientes:
        dias_por_area[dep.area or "Sin área"].append((ahora - dep.actualizado_en).days)
    pendientes_por_area = sorted(
        (
            {"area": area, "cantidad": len(dias), "antiguedad_promedio_dias": round(sum(dias) / len(dias), 1)}
            for area, dias in dias_por_area.items()
        ),
        key=lambda x: x["cantidad"],
        reverse=True,
    )
    todos_los_dias = [d for dias in dias_por_area.values() for d in dias]

    # Vigencia por área: cuántos registros llevan más de UMBRAL_ROJO_DIAS sin
    # actualizarse -- mismo umbral y mismo campo (actualizado_en) que ya usa
    # el semáforo rojo/ámbar/verde de la tabla de dependencias (ver
    # semaforoVigencia() en admin.js), pero agregado por área para poder
    # avisar "tu área tiene N registros para revisar" sin que nadie tenga que
    # entrar a mirar fila por fila. Sobre TODAS las dependencias (no solo las
    # publicadas), igual que ese semáforo, que se calcula para cualquier fila
    # visible en la tabla sin importar su estado.
    todas = db.query(models.Dependencia).all()
    UMBRAL_ROJO_DIAS = 180
    desactualizados_por_area = defaultdict(int)
    for dep in todas:
        if (ahora - dep.actualizado_en).days > UMBRAL_ROJO_DIAS:
            desactualizados_por_area[dep.area or "Sin área"] += 1
    vigencia_por_area = sorted(
        ({"area": area, "cantidad": cantidad} for area, cantidad in desactualizados_por_area.items()),
        key=lambda x: x["cantidad"],
        reverse=True,
    )

    # Completitud de datos por área, solo sobre lo YA publicado -- "pendientes
    # por área" ya cubre lo que falta aprobar; esto cubre lo que falta
    # TERMINAR de llenar en lo que el público ya está viendo (horario,
    # teléfono, algún dato de accesibilidad confirmado). No nombra
    # dependencias puntuales, mismo criterio que "pendientes por área".
    activas = db.query(models.Dependencia).filter(models.Dependencia.estado == "activo").all()
    datos_por_area = defaultdict(lambda: {"total": 0, "completos": 0})
    for dep in activas:
        grupo = datos_por_area[dep.area or "Sin área"]
        grupo["total"] += 1
        campos = (bool(dep.horario), bool(dep.telefono), bool(dep.rampa or dep.ascensor or dep.banio_accesible))
        grupo["completos"] += sum(campos)
    completitud_por_area = sorted(
        (
            {
                "area": area,
                "activas": datos["total"],
                "porcentaje_completo": round((datos["completos"] / (datos["total"] * 3)) * 100, 1),
            }
            for area, datos in datos_por_area.items()
        ),
        key=lambda x: x["porcentaje_completo"],
    )
    total_activas = len(activas)
    total_completos = sum(datos["completos"] for datos in datos_por_area.values())
    porcentaje_completitud_global = (
        round((total_completos / (total_activas * 3)) * 100, 1) if total_activas else None
    )

    return {
        "total_consultas": total,
        "consultas_resueltas": encontradas,
        "consultas_sin_resultado": sin_resultado,
        "porcentaje_resueltas": round((encontradas / total) * 100, 1) if total else None,
        # % de ciudadanos que encontraron lo que buscaban en su primera consulta
        # (sin necesitar reformular ni ser derivados). Misma fórmula que
        # "porcentaje_resueltas" hoy -- se expone aparte porque es la métrica
        # que el proyecto usa como meta institucional (ver Plan Maestro,
        # sección "Métricas de Éxito": meta declarada >80%).
        "primera_orientacion_correcta": round((encontradas / total) * 100, 1) if total else None,
        "respuestas_satisfaccion": con_respuesta,
        "porcentaje_satisfaccion": round((satisfechas / con_respuesta) * 100, 1) if con_respuesta else None,
        "top_consultas": [{"consulta": t, "veces": n} for t, n in top],
        "top_consultas_sin_resultado": [{"consulta": t, "veces": n} for t, n in top_sin_resultado],
        # ── Indicadores de uso y accesibilidad (sección 30) ──
        "porcentaje_modo_accesible": _porcentaje(models.ConsultaLog.modo_accesible.is_(True)),
        "porcentaje_via_voz": _porcentaje(models.ConsultaLog.via_voz.is_(True)),
        "porcentaje_sobre_accesibilidad": _porcentaje(models.ConsultaLog.sobre_accesibilidad.is_(True)),
        "consultas_por_sede": [{"sede": s, "veces": n} for s, n in por_sede],
        "consultas_por_area": [{"area": a or "Sin área", "veces": n} for a, n in por_area],
        "consultas_por_tipo": [{"tipo": t, "veces": n} for t, n in por_tipo],
        # ── Salud del flujo editorial ──
        "pendientes_total": len(pendientes),
        "pendientes_antiguedad_promedio_dias": round(sum(todos_los_dias) / len(todos_los_dias), 1) if todos_los_dias else None,
        "pendientes_por_area": pendientes_por_area,
        # ── Vigencia: registros que llevan más de 180 días sin actualizar ──
        "vigencia_total": sum(desactualizados_por_area.values()),
        "vigencia_por_area": vigencia_por_area,
        # ── Completitud de datos ya publicados (horario, teléfono, algún
        # dato de accesibilidad confirmado), por área ──
        "porcentaje_completitud_global": porcentaje_completitud_global,
        "completitud_por_area": completitud_por_area,
    }


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
        ("% primera orientación correcta", datos["primera_orientacion_correcta"]),
        ("Respuestas de satisfacción", datos["respuestas_satisfaccion"]),
        ("% de satisfacción (de quienes respondieron)", datos["porcentaje_satisfaccion"]),
        ("% en modo accesible", datos["porcentaje_modo_accesible"]),
        ("% por voz", datos["porcentaje_via_voz"]),
        ("% sobre accesibilidad", datos["porcentaje_sobre_accesibilidad"]),
        ("Dependencias pendientes de aprobar", datos["pendientes_total"]),
        ("Antigüedad promedio de lo pendiente (días)", datos["pendientes_antiguedad_promedio_dias"]),
        ("Registros sin actualizar hace más de 180 días", datos["vigencia_total"]),
        ("% completitud de datos ya publicados", datos["porcentaje_completitud_global"]),
    ]
    resumen.append(["Indicador", "Valor"])
    for celda in resumen[4]:
        celda.font = Font(bold=True)
    for fila in filas_resumen:
        resumen.append(fila)
    resumen.column_dimensions["A"].width = 45
    resumen.column_dimensions["B"].width = 18

    hoja_con_tabla(wb, "Consultas más frecuentes", ["Consulta", "Veces"],
                [(t["consulta"], t["veces"]) for t in datos["top_consultas"]])
    hoja_con_tabla(wb, "Búsquedas sin resultado", ["Consulta", "Veces"],
                [(t["consulta"], t["veces"]) for t in datos["top_consultas_sin_resultado"]])
    hoja_con_tabla(wb, "Por sede", ["Sede", "Veces"],
                [(c["sede"], c["veces"]) for c in datos["consultas_por_sede"]])
    hoja_con_tabla(wb, "Por área", ["Área", "Veces"],
                [(c["area"], c["veces"]) for c in datos["consultas_por_area"]])
    hoja_con_tabla(wb, "Por tipo", ["Tipo", "Veces"],
                [(c["tipo"], c["veces"]) for c in datos["consultas_por_tipo"]])
    hoja_con_tabla(wb, "Pendientes por área", ["Área", "Cantidad", "Antigüedad promedio (días)"],
                [(p["area"], p["cantidad"], p["antiguedad_promedio_dias"]) for p in datos["pendientes_por_area"]])
    hoja_con_tabla(wb, "Vigencia por área", ["Área", "Sin actualizar hace más de 180 días"],
                [(v["area"], v["cantidad"]) for v in datos["vigencia_por_area"]])
    hoja_con_tabla(wb, "Completitud por área", ["Área", "Dependencias activas", "% completo"],
                [(c["area"], c["activas"], c["porcentaje_completo"]) for c in datos["completitud_por_area"]])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    nombre_archivo = f"reporte_justicia_orienta_{ahora_utc().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )
