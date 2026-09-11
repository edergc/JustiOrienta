import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db
from app.excel_utils import hoja_con_tabla
from app.models.base import ahora_utc

router = APIRouter()


@router.get("", response_model=schemas.AuditoriaListaOut)
def ver_auditoria(
    usuario_dni: Optional[str] = None,
    entidad: Optional[str] = None,
    accion: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    skip: int = 0,
    limite: int = 100,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_lectura_auditoria),
):
    limite = min(limite, 500)
    items = crud.auditoria.listar(
        db, usuario_dni=usuario_dni, entidad=entidad, accion=accion, desde=desde, hasta=hasta,
        skip=skip, limite=limite,
    )
    total = crud.auditoria.contar(db, usuario_dni=usuario_dni, entidad=entidad, accion=accion, desde=desde, hasta=hasta)
    return schemas.AuditoriaListaOut(
        items=[schemas.AuditoriaOut.model_validate(a) for a in items],
        total=total, skip=skip, limite=limite,
    )


@router.get("/exportar.xlsx")
def exportar_auditoria(
    usuario_dni: Optional[str] = None,
    entidad: Optional[str] = None,
    accion: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_lectura_auditoria),
):
    """Mismos filtros que el listado, pero sin paginar (hasta 5000 filas) --
    pensado para entregarle al equipo de TI/auditor un archivo con exactamente
    el recorte que se le haya pedido revisar, sin que tenga que armarlo a
    mano juntando páginas del panel."""
    registros = crud.auditoria.listar(
        db, usuario_dni=usuario_dni, entidad=entidad, accion=accion, desde=desde, hasta=hasta,
        skip=0, limite=5000,
    )

    wb = Workbook()
    wb.remove(wb.active)
    hoja_con_tabla(
        wb, "Auditoría",
        ["Fecha", "Usuario (DNI)", "Entidad", "ID entidad", "Acción", "Detalle", "IP de origen"],
        [
            (r.fecha.strftime("%Y-%m-%d %H:%M:%S"), r.usuario_dni or "", r.entidad or "",
             r.entidad_id if r.entidad_id is not None else "", r.accion, r.detalle or "", r.ip_origen or "")
            for r in registros
        ],
    )

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    nombre_archivo = f"auditoria_justicia_orienta_{ahora_utc().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )
