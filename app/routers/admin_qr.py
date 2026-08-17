"""Generación de códigos QR para imprimir y pegar en carteles físicos de
cada sede/dependencia -- apuntan al sitio público con el contexto ya
resuelto (?sede=<id> o ?dependencia=<id>), así la persona no tiene que
escribir nada al llegar. Todo generado localmente con la librería `qrcode`,
sin depender de ningún servicio externo de terceros."""
import io

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import crud, security
from app.database import get_db

router = APIRouter()


def _png_qr(url: str) -> bytes:
    img = qrcode.make(url, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@router.get("/sede/{sede_id}")
def qr_sede(
    sede_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    sede = crud.sedes.obtener(db, sede_id)
    if not sede:
        raise HTTPException(404, "Sede no encontrada")
    url = f"{str(request.base_url).rstrip('/')}/?sede={sede_id}"
    return Response(content=_png_qr(url), media_type="image/png")


@router.get("/dependencia/{dep_id}")
def qr_dependencia(
    dep_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    url = f"{str(request.base_url).rstrip('/')}/?dependencia={dep_id}"
    return Response(content=_png_qr(url), media_type="image/png")
