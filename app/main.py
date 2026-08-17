from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import admin, auth, public

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# MVP: crea las tablas directamente (sin Alembic todavía). Para un despliegue
# institucional definitivo, sumar migraciones versionadas es la siguiente mejora.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Justicia Orienta",
    description="Orientador ciudadano accesible para la Corte Superior de Justicia de Lima.",
    version="0.1.0-piloto",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.include_router(auth.router, prefix="/api/auth", tags=["autenticación"])
app.include_router(public.router, prefix="/api", tags=["público"])
app.include_router(admin.router, prefix="/api/admin", tags=["administración"])

app.mount("/css", StaticFiles(directory=STATIC_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=STATIC_DIR / "js"), name="js")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin", include_in_schema=False)
def admin_panel():
    return FileResponse(STATIC_DIR / "admin.html")
