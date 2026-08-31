from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

ESTADOS_SOLICITUD_ATENCION = ("recibida", "derivada", "en_atencion", "respondida", "cerrada")


class SolicitudAtencionCreate(BaseModel):
    nombre_contacto: str
    telefono: Optional[str] = None
    correo: Optional[str] = None
    motivo: str

    @field_validator("motivo")
    @classmethod
    def _motivo_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Cuéntanos brevemente qué necesitas.")
        return v.strip()

    @model_validator(mode="after")
    def _al_menos_un_contacto(self) -> "SolicitudAtencionCreate":
        # model_validator (no field_validator) a propósito: un field_validator
        # sobre "correo" no se ejecuta cuando ambos campos vienen AUSENTES del
        # payload (Pydantic no valida un default no provisto, solo un valor
        # explícito) -- con eso, omitir los dos campos por completo se colaba
        # sin error, justo el caso que más importa bloquear.
        if not (self.telefono or "").strip() and not (self.correo or "").strip():
            raise ValueError("Déjanos un teléfono o un correo para poder contactarte.")
        return self


class SolicitudAtencionUpdate(BaseModel):
    area: Optional[str] = None
    estado: Optional[Literal["recibida", "derivada", "en_atencion", "respondida", "cerrada"]] = None
    comentario: Optional[str] = None


class SolicitudAtencionPublicaOut(BaseModel):
    """Lo que ve el ciudadano al crear la solicitud o al consultarla por
    código -- sin el comentario interno del área (notas de triage que no
    necesariamente están redactadas para el público)."""

    model_config = ConfigDict(from_attributes=True)

    codigo: str
    estado: str
    area: Optional[str] = None
    creado_en: datetime
    actualizado_en: datetime


class SolicitudAtencionOut(BaseModel):
    """Vista completa, solo para el panel de administración."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre_contacto: str
    telefono: Optional[str] = None
    correo: Optional[str] = None
    motivo: str
    area: Optional[str] = None
    estado: str
    comentario: Optional[str] = None
    creado_en: datetime
    actualizado_en: datetime
