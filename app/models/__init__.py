"""Agrega todos los modelos en un solo lugar -- importarlos aquí es lo que
registra cada tabla en Base.metadata, algo que Alembic necesita para poder
autogenerar migraciones."""
from app.models.base import Base, TimestampMixin, normalizar
from app.models.sede import Sede
from app.models.edificio import Edificio
from app.models.dependencia import Dependencia
from app.models.servicio import Servicio
from app.models.alias import Alias
from app.models.usuario import Usuario, Rol
from app.models.auditoria import Auditoria
from app.models.consulta import ConsultaLog

__all__ = [
    "Base", "TimestampMixin", "normalizar",
    "Sede", "Edificio", "Dependencia", "Servicio", "Alias",
    "Usuario", "Rol", "Auditoria", "ConsultaLog",
]
