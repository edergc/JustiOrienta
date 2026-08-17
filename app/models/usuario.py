import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String

from app.models.base import Base, ahora_utc


class Rol(str, enum.Enum):
    """Cuatro roles, tal como se definieron en el diseño de gobernanza:
    - admin: control total, incluida la administración de sedes y usuarios.
    - gestor: crea/edita el contenido de su propia área -- nunca publica solo.
    - validador: revisa y aprueba (publica) el contenido de su área.
    - auditor: solo lectura de auditoría e indicadores, ninguna escritura.
    """

    admin = "admin"
    gestor = "gestor"
    validador = "validador"
    auditor = "auditor"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    # DNI (Documento Nacional de Identidad, 8 dígitos) -- identificador de acceso,
    # en vez de correo: es el dato que toda persona en Perú tiene con certeza,
    # a diferencia de una cuenta de correo institucional.
    dni = Column(String(8), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    rol = Column(Enum(Rol), nullable=False, default=Rol.gestor)
    area = Column(String(150), nullable=True)  # obligatorio en la práctica para gestor/validador
    activo = Column(Boolean, default=True)
    ultimo_acceso = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, default=ahora_utc)

    def __repr__(self):
        return f"<Usuario {self.dni} ({self.rol})>"
