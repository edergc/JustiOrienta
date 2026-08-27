"""Configuración centralizada (patrón profesional estándar: nada de os.getenv
disperso por el código). Lee de variables de entorno y, si existe, de un
archivo .env -- ver .env.example."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Justicia Orienta"
    app_version: str = "0.2.0-piloto"
    entorno: str = "desarrollo"  # desarrollo | produccion

    # SQLite por defecto (cero instalación). PostgreSQL en producción sin
    # cambiar código: postgresql+psycopg2://usuario:clave@host:5432/db
    database_url: str = "sqlite:///./justicia_orienta.db"

    justicia_orienta_secret: str = "cambia-esta-clave-antes-de-produccion"
    token_expire_minutes: int = 8 * 60

    # Orígenes permitidos si el frontend llega a separarse en otro proceso/puerto.
    # Hoy el frontend se sirve desde el mismo proceso, así que esto no aplica
    # todavía en la práctica, pero queda listo para cuando se necesite.
    cors_origins: list[str] = ["http://127.0.0.1:8743", "http://localhost:8743"]

    # Correo saliente, solo para el enlace de "olvidé mi contraseña" -- sin
    # servicio de terceros, un SMTP cualquiera (institucional o de prueba).
    # Si smtp_host queda vacío (como en desarrollo local sin configurar
    # nada), no falla: el correo se registra en el log en vez de enviarse
    # de verdad, para poder probar el flujo sin credenciales reales.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_usuario: str = ""
    smtp_password: str = ""
    smtp_remitente: str = "Justicia Orienta <no-responder@justiciaorienta.local>"

    # Para armar el enlace del correo (…/admin?reset=token) -- en producción
    # debe ser la URL pública real del sitio.
    url_publica: str = "http://localhost:8743"


settings = Settings()
