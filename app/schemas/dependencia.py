from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.auditoria import AuditoriaOut
from app.schemas.edificio import EdificioOut
from app.schemas.sede import SedeOut
from app.schemas.servicio import ServicioOut


class DependenciaBase(BaseModel):
    tipo: Literal["jurisdiccional", "administrativa", "servicio"]
    categoria: Optional[str] = None
    nombre: str
    sede_id: int
    edificio_id: Optional[int] = None
    piso: Optional[str] = None
    oficina: Optional[str] = None
    horario: Optional[str] = None
    servicios: Optional[str] = None
    requisitos: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    rampa: bool = False
    ascensor: bool = False
    banio_accesible: bool = False
    ruta_accesible: bool = False
    instrucciones_internas: Optional[str] = None
    estado: Literal["revision", "activo", "inactivo"] = "revision"
    area: Optional[str] = None
    responsable_validar: Optional[str] = None
    titular: Optional[str] = None


class DependenciaCreate(DependenciaBase):
    alias: str = ""  # separados por coma, igual que la plantilla Excel


class DependenciaUpdate(DependenciaCreate):
    pass


class DependenciaOut(DependenciaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alias: list[str] = []
    sede: Optional[SedeOut] = None
    edificio: Optional[EdificioOut] = None
    servicios_detalle: list[ServicioOut] = []
    actualizado_en: Optional[datetime] = None

    @field_validator("alias", mode="before")
    @classmethod
    def _alias_a_texto(cls, v):
        if v and hasattr(v[0] if len(v) else None, "alias"):
            return [a.alias for a in v]
        return v


class DependenciaListaOut(BaseModel):
    items: list[DependenciaOut]
    total: int
    skip: int
    limite: int


class HistorialDependenciaOut(BaseModel):
    """Responde "por que el sistema mostro esto": quien publico el dato
    vigente (auditoria) y cuanto se uso como respuesta a un ciudadano
    (consultas) -- las dos mitades de la trazabilidad de la orientacion,
    en una sola vista en vez de dos tablas separadas."""

    dependencia_id: int
    nombre: str
    estado: str
    actualizado_en: Optional[datetime] = None
    cambios: list[AuditoriaOut]
    veces_mostrada_como_respuesta: int
    ultima_vez_mostrada: Optional[datetime] = None
