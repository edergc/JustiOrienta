import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import SECRETO_POR_DEFECTO, settings
from app.routers import (
    admin_auditoria,
    admin_cobertura,
    admin_dependencias,
    admin_edificios,
    admin_mapa,
    admin_metricas,
    admin_qr,
    admin_sedes,
    admin_solicitudes_atencion,
    admin_usuarios,
    auth,
    public,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
API_PREFIX = "/api/v1"
LOGS_DIR = BASE_DIR.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Consola (para desarrollo) + archivo rotativo de 1 MB x 5 respaldos (para
# poder revisar errores en producción sin depender de la consola, que no
# persiste al reiniciar el proceso).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(LOGS_DIR / "justicia_orienta.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"),
    ],
)
logger = logging.getLogger("justicia_orienta")

# Sin esto, desplegar en produccion sin fijar JUSTICIA_ORIENTA_SECRET queda en
# silencio con la clave de relleno del repo publico -- cualquiera podria
# forjar un JWT valido (incluido uno de admin) sin que nada lo avise. Se
# revienta el arranque a proposito: un 500 en cada request seria mas facil de
# pasar por alto que el proceso negandose a levantar.
if settings.entorno == "produccion" and settings.justicia_orienta_secret == SECRETO_POR_DEFECTO:
    raise RuntimeError(
        "JUSTICIA_ORIENTA_SECRET sigue en su valor de relleno con ENTORNO=produccion. "
        "Define una clave propia y secreta (ej. con `python -c \"import secrets; print(secrets.token_urlsafe(48))\"`) "
        "antes de levantar el servicio."
    )

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

# Sin CDN ni recursos de terceros en todo el frontend (css/js propios, sin
# fuentes externas) -- permite un CSP estricto: "self" para todo, salvo
# style-src ("unsafe-inline" porque el HTML usa bastantes atributos
# style="" propios, ninguno de terceros) e img-src (agrega blob: porque el
# QR y las descargas del panel se abren con URL.createObjectURL). Ademas de
# CSP, cierra otros vectores clasicos: X-Frame-Options evita que otro sitio
# embeba el panel en un iframe (clickjacking), y Permissions-Policy solo deja
# microfono habilitado (lo usa la busqueda por voz) y bloquea el resto.
_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


@app.middleware("http")
async def cabeceras_seguridad(request: Request, call_next):
    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    respuesta.headers["Permissions-Policy"] = "microphone=(self), camera=(), geolocation=(), payment=()"
    respuesta.headers["Content-Security-Policy"] = _CSP
    # HSTS: el navegador solo la respeta sobre HTTPS real, asi que no rompe
    # nada servir esto tambien en HTTP (desarrollo/LAN) -- pero sí protege en
    # cuanto el sitio quede detras de un proxy con TLS en produccion.
    respuesta.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return respuesta


@app.exception_handler(RequestValidationError)
async def error_validacion(request: Request, exc: RequestValidationError):
    """Respuesta consistente y en español ante datos de entrada inválidos.

    jsonable_encoder es necesario y no un simple exc.errors(): Pydantic v2
    incluye la excepción original en errors()[i]["ctx"]["error"] (por ejemplo
    el ValueError de un field_validator), y json.dumps no sabe serializar un
    objeto de excepción -- sin esto, un dato inválido devolvía 500 en vez
    de 422.
    """
    return JSONResponse(
        status_code=422,
        content={"detail": "Los datos enviados no son válidos.", "errores": jsonable_encoder(exc.errors())},
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
app.include_router(admin_qr.router, prefix=f"{API_PREFIX}/admin/qr", tags=["admin-qr"])
app.include_router(admin_cobertura.router, prefix=f"{API_PREFIX}/admin/cobertura", tags=["admin-cobertura"])
app.include_router(admin_mapa.router, prefix=f"{API_PREFIX}/admin/mapa", tags=["admin-mapa"])
app.include_router(
    admin_solicitudes_atencion.router,
    prefix=f"{API_PREFIX}/admin/solicitudes-atencion",
    tags=["admin-solicitudes-atencion"],
)

app.mount("/css", StaticFiles(directory=STATIC_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=STATIC_DIR / "js"), name="js")
app.mount("/icons", StaticFiles(directory=STATIC_DIR / "icons"), name="icons")
app.mount("/img", StaticFiles(directory=STATIC_DIR / "img"), name="img")


@app.get("/manifest.json", include_in_schema=False)
def manifest():
    return FileResponse(STATIC_DIR / "manifest.json")


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    # Servido en la raíz (no bajo /js) a propósito: el alcance ("scope") de
    # un service worker es, por defecto, la carpeta desde la que se sirve
    # -- si viviera en /js/sw.js solo podría controlar /js/, no toda la app.
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


@app.get("/presentacion-ceremonia.html", include_in_schema=False)
def presentacion_ceremonia():
    # Desactivada tras la ceremonia. Se deja la ruta (en vez de borrarla) para
    # poder reactivarla facil si se necesita de nuevo.
    return JSONResponse(status_code=404, content={"detail": "La presentación no está disponible en este momento."})


# Un solo numero de version para todo /css y /js, calculado una vez cuando
# arranca el proceso -- cada deploy (o cada reinicio local) es un proceso
# nuevo, asi que el numero cambia solo, sin que nadie tenga que acordarse de
# subir a mano un "?v=8" en el HTML cada vez que se edita un archivo estatico
# (fuente real de bugs de "cache vieja" durante esta sesion).
_VERSION_ESTATICA = str(int(time.time()))


def _pagina_con_version(nombre_archivo: str) -> HTMLResponse:
    html = (STATIC_DIR / nombre_archivo).read_text(encoding="utf-8")
    # no-store, no solo no-cache: esta respuesta no trae ETag ni
    # Last-Modified, asi que "no-cache" (que solo exige revalidar antes de
    # reusar una copia) queda ambiguo sin nada con que revalidar -- en la
    # practica, algunos navegadores igual sirven la copia vieja. no-store
    # prohibe guardar la respuesta por completo, sin esa ambiguedad: el
    # propio HTML de "/" o "/admin" (con la referencia a JS/CSS con la
    # version correcta) siempre se pide de nuevo.
    return HTMLResponse(
        html.replace("{{V}}", _VERSION_ESTATICA),
        headers={"Cache-Control": "no-store"},
    )


@app.get("/", include_in_schema=False)
def index():
    return _pagina_con_version("index.html")


@app.get("/admin", include_in_schema=False)
def admin_panel():
    return _pagina_con_version("admin.html")
