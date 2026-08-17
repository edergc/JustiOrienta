import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import (
    admin_auditoria,
    admin_dependencias,
    admin_edificios,
    admin_metricas,
    admin_sedes,
    admin_usuarios,
    auth,
    public,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("justicia_orienta")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
API_PREFIX = "/api/v1"

app = FastAPI(
    title=settings.app_name,
    description="Orientador ciudadano accesible para la Corte Superior de Justicia de Lima.",
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def error_validacion(request: Request, exc: RequestValidationError):
    """Respuesta consistente y en español ante datos de entrada inválidos."""
    return JSONResponse(
        status_code=422,
        content={"detail": "Los datos enviados no son válidos.", "errores": exc.errors()},
    )


@app.exception_handler(Exception)
async def error_no_manejado(request: Request, exc: Exception):
    logger.exception("Error no manejado en %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Ocurrió un error inesperado en el servidor."})


app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["autenticación"])
app.include_router(public.router, prefix=API_PREFIX, tags=["público"])
app.include_router(admin_dependencias.router, prefix=f"{API_PREFIX}/admin", tags=["admin-dependencias"])
app.include_router(admin_sedes.router, prefix=f"{API_PREFIX}/admin/sedes", tags=["admin-sedes"])
app.include_router(admin_edificios.router, prefix=f"{API_PREFIX}/admin/edificios", tags=["admin-edificios"])
app.include_router(admin_usuarios.router, prefix=f"{API_PREFIX}/admin/usuarios", tags=["admin-usuarios"])
app.include_router(admin_auditoria.router, prefix=f"{API_PREFIX}/admin/auditoria", tags=["admin-auditoria"])
app.include_router(admin_metricas.router, prefix=f"{API_PREFIX}/admin/metricas", tags=["admin-métricas"])

app.mount("/css", StaticFiles(directory=STATIC_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=STATIC_DIR / "js"), name="js")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin", include_in_schema=False)
def admin_panel():
    return FileResponse(STATIC_DIR / "admin.html")
