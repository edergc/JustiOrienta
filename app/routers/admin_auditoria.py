from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.AuditoriaOut])
def ver_auditoria(
    limite: int = 100,
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_lectura_auditoria),
):
    return crud.auditoria.listar(db, limite=min(limite, 500))
