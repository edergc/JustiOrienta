🚀 PROMPT DE IMPLEMENTACIÓN — JUSTICIA ORIENTA v1.0
Código Fuente para una IA o Ingeniero de Software
═══════════════════════════════════════════════════════════════
INSTRUCCIÓN MAESTRA DE IMPLEMENTACIÓN
═══════════════════════════════════════════════════════════════
ROL: Actúa como un equipo de desarrollo full-stack senior especializado en innovación pública, accesibilidad y diseño de servicios centrados en el ciudadano.

MISIÓN: Implementar el proyecto JUSTICIA ORIENTA — Un orientador judicial digital, accesible e inclusivo para la Corte Superior de Justicia de Lima.

ENTREGA: Código fuente completo, documentación, scripts de instalación y datos de ejemplo funcionales.

PLAZO ESTIMADO: 4-6 semanas (Fase MVP)

═══════════════════════════════════════════════════════════════
1. CONTEXTO DEL PROYECTO (LEER OBLIGATORIAMENTE)
═══════════════════════════════════════════════════════════════
JUSTICIA ORIENTA es una buena práctica de atención al ciudadano, no solo una aplicación. El objetivo es que cualquier persona pueda llegar a la Corte Superior de Justicia de Lima y, sin conocer su estructura interna, pueda:

Descubrir qué necesita hacer

Encontrar el servicio/área/dependencia correspondiente

Conocer su ubicación exacta (sede, piso, oficina)

Obtener una ruta para llegar

Conocer requisitos, horarios y canales alternativos

Recibir orientación accesible (voz, alto contraste, lectura)

PRINCIPIO FUNDAMENTAL: La persona no debe necesitar conocer la estructura de la Corte. El sistema debe interpretar su necesidad en lenguaje natural y proporcionar una respuesta clara y accionable.

FRASE CONCEPTUAL: "No necesitas conocer cómo funciona la Corte para encontrar el servicio que necesitas."

═══════════════════════════════════════════════════════════════
2. ARQUITECTURA TÉCNICA
═══════════════════════════════════════════════════════════════
2.1 Stack Tecnológico
text
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND                                │
│  React 18 + TypeScript + Vite + Tailwind CSS 3              │
│  React Router Dom (v6)                                      │
│  React Hook Form + Zod (validación)                         │
│  Web Speech API (voz)                                       │
│  Axios (HTTP client)                                        │
│  Lucide React (iconos)                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND                                 │
│  Python 3.11 + FastAPI                                      │
│  SQLAlchemy 2.0 (ORM) + Alembic (migraciones)              │
│  Pydantic v2 (validación)                                   │
│  PostgreSQL 15 + pg_trgm (búsqueda)                        │
│  JWT (autenticación)                                        │
│  Python-multipart (archivos)                                │
│  Logging + Sentry (opcional)                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    INFRAESTRUCTURA                           │
│  Servidor: Linux (Ubuntu 22.04 LTS)                        │
│  Database: PostgreSQL 15                                    │
│  Web Server: Nginx (proxy)                                  │
│  SSL: Let's Encrypt                                        │
│  Backup: pg_dump diario                                    │
└─────────────────────────────────────────────────────────────┘
2.2 Estructura de Directorios
text
justicia-orienta/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py
│   │   │   │   │   ├── sedes.py
│   │   │   │   │   ├── dependencias.py
│   │   │   │   │   ├── servicios.py
│   │   │   │   │   ├── busqueda.py
│   │   │   │   │   ├── orientacion.py
│   │   │   │   │   ├── metricas.py
│   │   │   │   │   └── auditoria.py
│   │   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── models/
│   │   │   ├── sede.py
│   │   │   ├── edificio.py
│   │   │   ├── dependencia.py
│   │   │   ├── servicio.py
│   │   │   ├── alias.py
│   │   │   ├── ruta.py
│   │   │   ├── usuario.py
│   │   │   ├── rol.py
│   │   │   ├── auditoria.py
│   │   │   ├── metrica.py
│   │   │   └── encuesta.py
│   │   ├── schemas/
│   │   │   ├── sede.py
│   │   │   ├── dependencia.py
│   │   │   ├── busqueda.py
│   │   │   ├── orientacion.py
│   │   │   ├── usuario.py
│   │   │   └── auditoria.py
│   │   ├── services/
│   │   │   ├── busqueda_service.py
│   │   │   ├── interpretacion_service.py
│   │   │   ├── orientacion_service.py
│   │   │   ├── geolocalizacion_service.py
│   │   │   ├── accesibilidad_service.py
│   │   │   └── metricas_service.py
│   │   ├── utils/
│   │   │   ├── normalizador.py
│   │   │   ├── validadores.py
│   │   │   └── helpers.py
│   │   └── main.py
│   ├── migrations/
│   │   └── versions/
│   ├── tests/
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_models/
│   ├── scripts/
│   │   ├── seed_data.py
│   │   ├── backup.sh
│   │   └── deploy.sh
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── dev.txt
│   │   └── prod.txt
│   ├── .env.example
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── Button/
│   │   │   │   ├── Card/
│   │   │   │   ├── Input/
│   │   │   │   ├── Modal/
│   │   │   │   └── Spinner/
│   │   │   ├── search/
│   │   │   │   ├── SearchBar/
│   │   │   │   ├── SearchResults/
│   │   │   │   ├── ResultCard/
│   │   │   │   └── VoiceInput/
│   │   │   ├── orientation/
│   │   │   │   ├── LocationDisplay/
│   │   │   │   ├── MapButton/
│   │   │   │   ├── AccessibilityInfo/
│   │   │   │   └── RouteInstructions/
│   │   │   ├── admin/
│   │   │   │   ├── Dashboard/
│   │   │   │   ├── SedeManager/
│   │   │   │   ├── DependenciaManager/
│   │   │   │   ├── AliasManager/
│   │   │   │   ├── AuditoriaLog/
│   │   │   │   └── MetricasPanel/
│   │   │   └── layout/
│   │   │       ├── Header/
│   │   │       ├── Footer/
│   │   │       └── AccessibilityMenu/
│   │   ├── pages/
│   │   │   ├── Home/
│   │   │   ├── Search/
│   │   │   ├── Result/
│   │   │   ├── Admin/
│   │   │   └── NotFound/
│   │   ├── hooks/
│   │   │   ├── useSearch.ts
│   │   │   ├── useVoice.ts
│   │   │   ├── useAccessibility.ts
│   │   │   └── useMetrics.ts
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── searchService.ts
│   │   │   ├── adminService.ts
│   │   │   └── authService.ts
│   │   ├── store/
│   │   │   ├── searchStore.ts
│   │   │   ├── accessibilityStore.ts
│   │   │   └── userStore.ts
│   │   ├── types/
│   │   │   ├── index.ts
│   │   │   ├── sede.ts
│   │   │   ├── dependencia.ts
│   │   │   └── busqueda.ts
│   │   ├── utils/
│   │   │   ├── formatters.ts
│   │   │   ├── validators.ts
│   │   │   └── accessibility.ts
│   │   ├── styles/
│   │   │   ├── globals.css
│   │   │   ├── tailwind.css
│   │   │   └── accessibility.css
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── public/
│   │   ├── icons/
│   │   ├── images/
│   │   └── qr/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── .env.example
│
├── docs/
│   ├── manual_usuario.md
│   ├── manual_administrador.md
│   ├── api_documentation.md
│   ├── deployment_guide.md
│   └── accessibility_guide.md
│
└── README.md
═══════════════════════════════════════════════════════════════
3. MODELO DE DATOS (SQLAlchemy)
═══════════════════════════════════════════════════════════════
3.1 Esquema completo de base de datos
python
# backend/app/models/base.py
from sqlalchemy import Column, DateTime, Integer, String, Boolean, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('usuarios.id'), nullable=True)

# ═══════════════════════════════════════════════════════════════

class Sede(Base, TimestampMixin):
    __tablename__ = 'sedes'
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    nombre_corto = Column(String(100))
    direccion = Column(Text, nullable=False)
    referencia = Column(Text)
    latitud = Column(Float)
    longitud = Column(Float)
    horario_atencion = Column(String(500))
    telefono = Column(String(20))
    email = Column(String(100))
    
    # Accesibilidad
    tiene_rampas = Column(Boolean, default=False)
    tiene_ascensor = Column(Boolean, default=False)
    tiene_banios_accesibles = Column(Boolean, default=False)
    tiene_estacionamiento = Column(Boolean, default=False)
    tiene_personal_asistencia = Column(Boolean, default=False)
    
    # Estado
    estado = Column(String(20), default='activo')  # activo, inactivo, mantenimiento
    
    # Relaciones
    edificios = relationship('Edificio', back_populates='sede', cascade='all, delete-orphan')
    dependencias = relationship('Dependencia', back_populates='sede')
    
    def __repr__(self):
        return f"<Sede {self.nombre}>"

# ═══════════════════════════════════════════════════════════════

class Edificio(Base, TimestampMixin):
    __tablename__ = 'edificios'
    
    id = Column(Integer, primary_key=True, index=True)
    sede_id = Column(Integer, ForeignKey('sedes.id'), nullable=False)
    nombre = Column(String(200), nullable=False)
    direccion = Column(Text)
    numero_pisos = Column(Integer, default=1)
    informacion = Column(Text)
    estado = Column(String(20), default='activo')
    
    # Relaciones
    sede = relationship('Sede', back_populates='edificios')
    dependencias = relationship('Dependencia', back_populates='edificio')
    
    def __repr__(self):
        return f"<Edificio {self.nombre}>"

# ═══════════════════════════════════════════════════════════════

class Dependencia(Base, TimestampMixin):
    __tablename__ = 'dependencias'
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    nombre_normalizado = Column(String(200), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)  # jurisdiccional, administrativa, servicio
    
    # Categorías
    categoria = Column(String(50))  # sala_superior, juzgado, unidad, coordinacion, etc.
    subcategoria = Column(String(50))  # civil, penal, laboral, etc.
    
    # Ubicación
    sede_id = Column(Integer, ForeignKey('sedes.id'), nullable=False)
    edificio_id = Column(Integer, ForeignKey('edificios.id'))
    piso = Column(String(20))
    oficina = Column(String(50))
    referencia_interna = Column(Text)
    
    # Información de contacto
    telefono = Column(String(20))
    correo = Column(String(100))
    horario_atencion = Column(String(500))
    
    # Descripción
    descripcion = Column(Text)
    servicios_ofrecidos = Column(Text)
    requisitos = Column(Text)
    documentos_necesarios = Column(Text)
    
    # Accesibilidad
    es_accesible = Column(Boolean, default=False)
    tiene_rampa = Column(Boolean, default=False)
    tiene_ascensor = Column(Boolean, default=False)
    tiene_silla_ruedas = Column(Boolean, default=False)
    
    # Estado
    estado = Column(String(20), default='activo')
    es_visible_publico = Column(Boolean, default=True)
    
    # Relaciones
    sede = relationship('Sede', back_populates='dependencias')
    edificio = relationship('Edificio', back_populates='dependencias')
    alias = relationship('Alias', back_populates='dependencia', cascade='all, delete-orphan')
    servicios = relationship('Servicio', back_populates='dependencia', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Dependencia {self.nombre}>"

# ═══════════════════════════════════════════════════════════════

class Servicio(Base, TimestampMixin):
    __tablename__ = 'servicios'
    
    id = Column(Integer, primary_key=True, index=True)
    dependencia_id = Column(Integer, ForeignKey('dependencias.id'), nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    canal = Column(String(50))  # presencial, virtual, telefónico
    horario = Column(String(500))
    requisitos = Column(Text)
    documentos = Column(Text)
    costo = Column(String(100))
    duracion_estimada = Column(String(100))
    estado = Column(String(20), default='activo')
    
    # Relaciones
    dependencia = relationship('Dependencia', back_populates='servicios')
    
    def __repr__(self):
        return f"<Servicio {self.nombre}>"

# ═══════════════════════════════════════════════════════════════

class Alias(Base, TimestampMixin):
    __tablename__ = 'alias'
    
    id = Column(Integer, primary_key=True, index=True)
    dependencia_id = Column(Integer, ForeignKey('dependencias.id'), nullable=False)
    alias = Column(String(200), nullable=False, index=True)
    tipo = Column(String(50), default='abreviatura')  # abreviatura, coloquial, error_comun
    prioridad = Column(Integer, default=1)  # 1 = mayor prioridad
    estado = Column(String(20), default='activo')
    
    # Relaciones
    dependencia = relationship('Dependencia', back_populates='alias')
    
    def __repr__(self):
        return f"<Alias {self.alias} -> {self.dependencia.nombre}>"

# ═══════════════════════════════════════════════════════════════

class Ruta(Base, TimestampMixin):
    __tablename__ = 'rutas'
    
    id = Column(Integer, primary_key=True, index=True)
    origen = Column(Text, nullable=False)  # Puede ser un punto de referencia
    destino_id = Column(Integer, ForeignKey('dependencias.id'), nullable=False)
    instrucciones = Column(Text)
    tipo = Column(String(50), default='peatonal')  # peatonal, vehicular
    distancia_aproximada = Column(String(50))
    tiempo_aproximado = Column(String(50))
    nivel_dificultad = Column(String(20))  # baja, media, alta
    es_accesible = Column(Boolean, default=False)
    estado = Column(String(20), default='activo')
    
    # Relaciones
    destino = relationship('Dependencia', foreign_keys=[destino_id])
    
    def __repr__(self):
        return f"<Ruta de {self.origen} a {self.destino.nombre}>"

# ═══════════════════════════════════════════════════════════════

class Usuario(Base, TimestampMixin):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    apellido = Column(String(200), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    rol_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    estado = Column(String(20), default='activo')
    ultimo_acceso = Column(DateTime)
    
    # Relaciones
    rol = relationship('Rol', back_populates='usuarios')
    
    def __repr__(self):
        return f"<Usuario {self.username}>"

# ═══════════════════════════════════════════════════════════════

class Rol(Base, TimestampMixin):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    permisos = Column(Text)  # Almacenar como JSON string
    estado = Column(String(20), default='activo')
    
    # Relaciones
    usuarios = relationship('Usuario', back_populates='rol')
    
    def __repr__(self):
        return f"<Rol {self.nombre}>"

# ═══════════════════════════════════════════════════════════════

class Auditoria(Base, TimestampMixin):
    __tablename__ = 'auditoria'
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    tabla = Column(String(50), nullable=False)
    registro_id = Column(Integer, nullable=False)
    accion = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE, PUBLISH
    campo = Column(String(50))
    valor_anterior = Column(Text)
    valor_nuevo = Column(Text)
    ip = Column(String(45))
    user_agent = Column(String(200))
    estado = Column(String(20), default='activo')
    
    def __repr__(self):
        return f"<Auditoria {self.tabla}:{self.registro_id} {self.accion}>"

# ═══════════════════════════════════════════════════════════════

class Metrica(Base, TimestampMixin):
    __tablename__ = 'metricas'
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False)  # busqueda, orientacion, accesibilidad, etc.
    dato = Column(Text)
    valor = Column(Integer)
    metadata = Column(Text)  # JSON con información adicional
    fecha = Column(DateTime, default=func.now(), nullable=False)
    sede_id = Column(Integer, ForeignKey('sedes.id'), nullable=True)
    dependencia_id = Column(Integer, ForeignKey('dependencias.id'), nullable=True)
    
    def __repr__(self):
        return f"<Metrica {self.tipo} - {self.fecha}>"

# ═══════════════════════════════════════════════════════════════

class Encuesta(Base, TimestampMixin):
    __tablename__ = 'encuestas'
    
    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(String(100), nullable=False)
    consulta_id = Column(Integer, ForeignKey('metricas.id'), nullable=True)
    encontro_lo_necesitaba = Column(String(10))  # si, parcial, no
    calificacion = Column(Integer)  # 1-5
    comentario = Column(Text)
    canal = Column(String(50))  # web, qr, voz
    
    def __repr__(self):
        return f"<Encuesta {self.sesion_id}>"
═══════════════════════════════════════════════════════════════
4. API ENDPOINTS (FastAPI)
═══════════════════════════════════════════════════════════════
4.1 Configuración principal
python
# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.core.security import get_current_user
from app.api.v1.endpoints import (
    auth, sedes, dependencias, servicios, 
    busqueda, orientacion, metricas, auditoria
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicio
    logger.info("🚀 Iniciando JUSTICIA ORIENTA API")
    yield
    # Fin
    logger.info("🛑 Cerrando JUSTICIA ORIENTA API")

app = FastAPI(
    title="JUSTICIA ORIENTA API",
    description="API de orientación judicial digital para la Corte Superior de Justicia de Lima",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Endpoints públicos
app.include_router(auth.router, prefix="/api/v1/auth", tags=["autenticacion"])
app.include_router(busqueda.router, prefix="/api/v1/search", tags=["busqueda"])
app.include_router(orientacion.router, prefix="/api/v1/orientacion", tags=["orientacion"])

# Endpoints protegidos (requieren autenticación)
app.include_router(
    sedes.router, 
    prefix="/api/v1/admin/sedes", 
    tags=["admin-sedes"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    dependencias.router,
    prefix="/api/v1/admin/dependencias",
    tags=["admin-dependencias"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    servicios.router,
    prefix="/api/v1/admin/servicios",
    tags=["admin-servicios"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    metricas.router,
    prefix="/api/v1/metricas",
    tags=["metricas"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    auditoria.router,
    prefix="/api/v1/auditoria",
    tags=["auditoria"],
    dependencies=[Depends(get_current_user)]
)

@app.get("/")
async def root():
    return {
        "proyecto": "JUSTICIA ORIENTA",
        "version": "1.0.0",
        "estado": "operativo",
        "documentacion": "/api/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
4.2 Endpoints de Búsqueda
python
# backend/app/api/v1/endpoints/busqueda.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from pydantic import BaseModel
from app.services.busqueda_service import BusquedaService
from app.services.interpretacion_service import InterpretacionService
from app.schemas.busqueda import (
    BusquedaRequest, 
    BusquedaResponse, 
    InterpretacionResponse
)
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

class BusquedaRequest(BaseModel):
    query: str
    tipo: Optional[str] = "ambos"  # dependencia, servicio, ambos
    limite: Optional[int] = 10
    incluir_inactivos: Optional[bool] = False

class BusquedaResponse(BaseModel):
    resultados: List[dict]
    interpretacion: dict
    total: int
    fallback: bool
    sugerencia: Optional[str] = None
    tiempo_ms: float

@router.post("/buscar", response_model=BusquedaResponse)
async def buscar(
    request: BusquedaRequest,
    db: Session = Depends(get_db)
):
    """
    Realiza una búsqueda en lenguaje natural sobre dependencias y servicios.
    """
    try:
        # 1. Interpretar la intención
        interpretacion = await InterpretacionService.interpretar(
            request.query, 
            db
        )
        
        # 2. Buscar resultados
        resultados = await BusquedaService.buscar(
            interpretacion=interpretacion,
            tipo=request.tipo,
            limite=request.limite,
            incluir_inactivos=request.incluir_inactivos,
            db=db
        )
        
        # 3. Generar respuesta
        return BusquedaResponse(
            resultados=resultados,
            interpretacion=interpretacion.dict(),
            total=len(resultados),
            fallback=len(resultados) == 0,
            sugerencia=BusquedaService.generar_sugerencia(resultados, request.query),
            tiempo_ms=0  # Calcular tiempo real
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la búsqueda: {str(e)}"
        )

@router.post("/interpretar", response_model=InterpretacionResponse)
async def interpretar(
    query: str = Query(..., description="Texto a interpretar"),
    db: Session = Depends(get_db)
):
    """
    Interpreta la intención del usuario sin realizar búsqueda.
    Útil para depuración y mejora del sistema.
    """
    try:
        interpretacion = await InterpretacionService.interpretar(query, db)
        return InterpretacionResponse(
            query=query,
            interpretacion=interpretacion.dict(),
            confianza=interpretacion.confianza
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la interpretación: {str(e)}"
        )

@router.get("/sugerencias")
async def sugerencias(
    q: str = Query(..., min_length=2),
    limite: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Obtiene sugerencias de búsqueda en tiempo real (autocomplete).
    """
    sugerencias = await BusquedaService.obtener_sugerencias(q, limite, db)
    return {"sugerencias": sugerencias}
4.3 Lógica de Interpretación (NLP)
python
# backend/app/services/interpretacion_service.py
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.alias import Alias
from app.models.dependencia import Dependencia
from app.utils.normalizador import Normalizador
import re
import logging

logger = logging.getLogger(__name__)

class InterpretacionService:
    @staticmethod
    async def interpretar(query: str, db: Session) -> Dict[str, Any]:
        """
        Interpreta la intención del usuario a partir de su consulta en lenguaje natural.
        
        Retorna:
        {
            "tipo": "localizar" | "orientar" | "informar" | "no_detectado",
            "entidad": "dependencia" | "servicio" | "ubicacion" | "ruta" | None,
            "palabras_clave": ["lista", "de", "palabras"],
            "dependencia_detectada": "11.º Juzgado Civil" | None,
            "confianza": 0.85,
            "ambiguo": False
        }
        """
        # 1. Normalizar
        texto_limpio = Normalizador.limpiar(query)
        texto_normalizado = Normalizador.normalizar(texto_limpio)
        palabras = Normalizador.tokenizar(texto_normalizado)
        
        # 2. Detectar tipo de intención
        tipo = InterpretacionService._detectar_tipo(texto_normalizado, palabras)
        
        # 3. Buscar dependencia por alias o nombre
        dependencia = InterpretacionService._buscar_dependencia(
            texto_normalizado, 
            palabras,
            db
        )
        
        # 4. Identificar servicio
        servicio = InterpretacionService._buscar_servicio(
            texto_normalizado,
            palabras,
            db
        )
        
        # 5. Detectar elementos de ubicación
        ubicacion = InterpretacionService._detectar_ubicacion(palabras)
        
        # 6. Construir resultado
        resultado = {
            "tipo": tipo,
            "entidad": InterpretacionService._determinar_entidad(dependencia, servicio),
            "palabras_clave": palabras[:10],  # Top 10 palabras
            "dependencia_detectada": dependencia.nombre if dependencia else None,
            "dependencia_id": dependencia.id if dependencia else None,
            "servicio_detectado": servicio.nombre if servicio else None,
            "servicio_id": servicio.id if servicio else None,
            "ubicacion": ubicacion,
            "confianza": InterpretacionService._calcular_confianza(dependencia, servicio, tipo),
            "ambiguo": InterpretacionService._es_ambiguo(dependencia, servicio),
            "query_original": query
        }
        
        logger.info(f"Interpretación: {resultado}")
        return resultado
    
    @staticmethod
    def _detectar_tipo(texto: str, palabras: list) -> str:
        """Detecta si la consulta es para localizar, orientar o informar"""
        localizar = ["dónde está", "dónde queda", "ubicación", "dirección", 
                     "en qué piso", "en qué oficina"]
        orientar = ["cómo llegar", "cómo ir", "ruta", "camino", "como llego"]
        informar = ["qué es", "qué hacen", "servicios", "horario", "requisitos"]
        
        texto_lower = texto.lower()
        
        if any(p in texto_lower for p in localizar):
            return "localizar"
        elif any(p in texto_lower for p in orientar):
            return "orientar"
        elif any(p in texto_lower for p in informar):
            return "informar"
        else:
            # Si no hay patrón claro, intentar inferir
            if any(p in ["dónde", "ubicación", "dirección", "piso", "oficina"] for p in palabras):
                return "localizar"
            elif any(p in ["cómo", "llegar", "ruta", "camino"] for p in palabras):
                return "orientar"
            else:
                return "informar"  # Default
    
    @staticmethod
    def _buscar_dependencia(texto: str, palabras: list, db: Session):
        """Busca una dependencia que coincida con la consulta"""
        # 1. Primero buscar en alias (coincidencia exacta)
        texto_normal = Normalizador.normalizar(texto)
        alias = db.query(Alias).filter(
            Alias.alias == texto_normal,
            Alias.estado == 'activo'
        ).first()
        
        if alias:
            return alias.dependencia
        
        # 2. Buscar en alias por coincidencia parcial (más flexible)
        # Usar pg_trgm para búsqueda fuzzy
        from sqlalchemy import text
        query_alias = text("""
            SELECT a.dependencia_id, a.alias, 
                   similarity(a.alias, :texto) as sim            FROM alias a
            WHERE a.estado = 'activo'
              AND similarity(a.alias, :texto) > 0.4
            ORDER BY sim DESC
            LIMIT 1
        """)
        result = db.execute(query_alias, {"texto": texto_normal}).first()
        
        if result:
            dependencia = db.query(Dependencia).get(result.dependencia_id)
            if dependencia and dependencia.estado == 'activo':
                return dependencia
        
        # 3. Buscar por nombre de dependencia
        dependencia = db.query(Dependencia).filter(
            Dependencia.nombre_normalizado == texto_normal,
            Dependencia.estado == 'activo'
        ).first()
        
        if dependencia:
            return dependencia
        
        # 4. Búsqueda por palabras clave en nombre
        # Dividir el texto en palabras y buscar cada una
        for palabra in palabras:
            if len(palabra) < 3:
                continue
            dependencia = db.query(Dependencia).filter(
                Dependencia.nombre_normalizado.contains(palabra),
                Dependencia.estado == 'activo'
            ).first()
            if dependencia:
                return dependencia
        
        return None
    
    @staticmethod
    def _buscar_servicio(texto: str, palabras: list, db: Session):
        """Busca un servicio que coincida con la consulta"""
        # Implementación similar a _buscar_dependencia pero para servicios
        # ... código similar ...
        return None
    
    @staticmethod
    def _detectar_ubicacion(palabras: list) -> Optional[Dict]:
        """Detecta menciones de ubicación en la consulta"""
        ubicacion = {}
        pisos = ["piso", "planta", "subsuelo", "sótano"]
        for i, p in enumerate(palabras):
            if p in pisos and i + 1 < len(palabras):
                try:
                    ubicacion["piso"] = int(palabras[i + 1])
                except:
                    ubicacion["piso"] = palabras[i + 1]
        
        if "sede" in palabras:
            ubicacion["sede_mencionada"] = True
        
        return ubicacion if ubicacion else None
    
    @staticmethod
    def _determinar_entidad(dependencia, servicio) -> str:
        """Determina qué tipo de entidad se ha encontrado"""
        if dependencia:
            return dependencia.tipo  # jurisdiccional, administrativa, servicio
        elif servicio:
            return "servicio"
        else:
            return "no_detectado"
    
    @staticmethod
    def _calcular_confianza(dependencia, servicio, tipo) -> float:
        """Calcula la confianza de la interpretación (0-1)"""
        confianza = 0.0
        if dependencia:
            confianza += 0.7
            if dependencia.nombre_normalizado:
                confianza += 0.2
        if servicio:
            confianza += 0.3
        if tipo != "no_detectado":
            confianza += 0.1
        return min(confianza, 1.0)
    
    @staticmethod
    def _es_ambiguo(dependencia, servicio) -> bool:
        """Detecta si hay ambigüedad en la interpretación"""
        # Si se encontraron ambas, podría ser ambiguo
        return dependencia is not None and servicio is not None

# ═══════════════════════════════════════════════════════════════
# Normalizador de texto
# ═══════════════════════════════════════════════════════════════

class Normalizador:
    @staticmethod
    def limpiar(texto: str) -> str:
        """Elimina caracteres especiales y espacios extra"""
        # Eliminar múltiples espacios
        texto = re.sub(r'\s+', ' ', texto)
        # Eliminar caracteres especiales pero mantener números y letras
        texto = re.sub(r'[^a-zA-Z0-9áéíóúüñÁÉÍÓÚÜÑ\s]', ' ', texto)
        return texto.strip()
    
    @staticmethod
    def normalizar(texto: str) -> str:
        """Normaliza texto: minúsculas, sin tildes, sin espacios extra"""
        # Minúsculas
        texto = texto.lower()
        # Reemplazar tildes
        tildes = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u', 'ñ': 'n'}
        for k, v in tildes.items():
            texto = texto.replace(k, v)
        # Eliminar espacios extra
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    
    @staticmethod
    def tokenizar(texto: str) -> list:
        """Divide el texto en tokens (palabras)"""
        # Eliminar palabras muy comunes (stopwords)
        stopwords = {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 
                     'de', 'del', 'al', 'en', 'por', 'para', 'con', 'sin',
                     'y', 'o', 'pero', 'que', 'como', 'donde', 'cuando'}
        tokens = [t for t in texto.split() if t not in stopwords and len(t) > 1]
        return tokens
═══════════════════════════════════════════════════════════════
5. COMPONENTES FRONTEND (React + TypeScript)
═══════════════════════════════════════════════════════════════
5.1 Componente de Búsqueda Principal
tsx
// frontend/src/components/search/SearchBar/SearchBar.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Search, Mic, MicOff, X } from 'lucide-react';
import { useVoice } from '../../../hooks/useVoice';
import { useAccessibility } from '../../../hooks/useAccessibility';
import { SearchBarProps } from '../../../types/busqueda';
import './SearchBar.css';

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  onVoiceInput,
  placeholder = '¿Qué necesitas?',
  isLoading = false,
  suggestions = [],
}) => {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { isListening, startListening, stopListening, transcript, error } = useVoice();
  const { highContrast, fontSize } = useAccessibility();

  // Efecto para manejar el transcript de voz
  useEffect(() => {
    if (transcript) {
      setQuery(transcript);
      if (onVoiceInput) {
        onVoiceInput(transcript);
      }
    }
  }, [transcript, onVoiceInput]);

  // Manejar envío
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
      setShowSuggestions(false);
    }
  };

  // Manejar cambio en el input
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    if (value.length > 1) {
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  // Manejar selección de sugerencia
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    onSearch(suggestion);
  };

  // Manejar tecla Escape
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowSuggestions(false);
      inputRef.current?.blur();
    }
  };

  // Manejar voz
  const handleVoiceToggle = async () => {
    if (isListening) {
      await stopListening();
    } else {
      await startListening();
    }
  };

  // Estilos accesibles
  const inputStyles = {
    fontSize: fontSize === 'large' ? '1.25rem' : 
              fontSize === 'xlarge' ? '1.5rem' : '1rem',
    backgroundColor: highContrast ? '#000' : 'white',
    color: highContrast ? '#fff' : '#000',
  };

  return (
    <div className="search-bar-container" role="search">
      <form onSubmit={handleSubmit} className="search-bar-form">
        <div className="search-bar-input-wrapper">
          <Search className="search-icon" aria-hidden="true" />
          
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleChange}
            onFocus={() => {
              setIsFocused(true);
              if (query.length > 1) setShowSuggestions(true);
            }}
            onBlur={() => {
              setTimeout(() => setShowSuggestions(false), 200);
            }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="search-bar-input"
            style={inputStyles}
            aria-label="Buscar dependencias o servicios"
            aria-describedby="search-help"
            aria-autocomplete="list"
            aria-expanded={showSuggestions}
            aria-controls="suggestions-list"
            disabled={isLoading}
            autoFocus
          />

          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="clear-button"
              aria-label="Limpiar búsqueda"
            >
              <X size={18} />
            </button>
          )}

          <button
            type="button"
            onClick={handleVoiceToggle}
            className={`voice-button ${isListening ? 'listening' : ''}`}
            aria-label={isListening ? 'Detener grabación' : 'Buscar por voz'}
            disabled={isLoading}
          >
            {isListening ? <MicOff size={20} /> : <Mic size={20} />}
          </button>
        </div>

        <button
          type="submit"
          className={`search-button ${isLoading ? 'loading' : ''}`}
          disabled={isLoading || !query.trim()}
          aria-label="Buscar"
        >
          {isLoading ? 'Buscando...' : 'Buscar'}
        </button>
      </form>

      {/* Sugerencias */}
      {showSuggestions && suggestions.length > 0 && (
        <ul
          id="suggestions-list"
          className="suggestions-list"
          role="listbox"
          aria-label="Sugerencias de búsqueda"
        >
          {suggestions.map((suggestion, index) => (
            <li
              key={index}
              role="option"
              className="suggestion-item"
              onClick={() => handleSuggestionClick(suggestion)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSuggestionClick(suggestion);
              }}
              tabIndex={0}
            >
              <Search size={14} aria-hidden="true" />
              {suggestion}
            </li>
          ))}
        </ul>
      )}

      {/* Indicador de carga */}
      {isLoading && (
        <div className="loading-indicator" aria-label="Cargando resultados">
          <span className="spinner" />
          <span>Buscando...</span>
        </div>
      )}

      {/* Mensaje de error de voz */}
      {error && (
        <div className="voice-error" role="alert">
          Error: {error}
        </div>
      )}

      <div id="search-help" className="sr-only">
        Escribe el nombre de una dependencia, servicio o lo que necesitas hacer.
        También puedes usar el botón de micrófono para buscar por voz.
      </div>
    </div>
  );
};
5.2 Componente de Resultados
tsx
// frontend/src/components/search/ResultCard/ResultCard.tsx
import React from 'react';
import { 
  MapPin, 
  Building2, 
  Clock, 
  Phone, 
  Mail, 
  Accessibility,
  ArrowRight,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { ResultCardProps } from '../../../types/busqueda';
import { MapButton } from '../../orientation/MapButton';
import { AccessibilityInfo } from '../../orientation/AccessibilityInfo';
import { useAccessibility } from '../../../hooks/useAccessibility';
import './ResultCard.css';

export const ResultCard: React.FC<ResultCardProps> = ({
  result,
  onExpand,
  onMapOpen,
  onVoiceRead,
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const { highContrast, fontSize, screenReader } = useAccessibility();

  const handleToggleExpand = () => {
    setIsExpanded(!isExpanded);
    if (onExpand) onExpand(result.id, !isExpanded);
  };

  const handleReadAloud = () => {
    if (onVoiceRead) {
      const texto = `
        ${result.nombre}.
        ${result.descripcion || ''}
        Ubicado en ${result.sede}, piso ${result.piso || 'no especificado'}.
        ${result.horario ? `Horario: ${result.horario}` : ''}
        ${result.telefono ? `Teléfono: ${result.telefono}` : ''}
        ${result.correo ? `Correo: ${result.correo}` : ''}
        ${result.es_accesible ? 'Esta dependencia es accesible.' : ''}
      `;
      onVoiceRead(texto);
    }
  };

  // Estilos accesibles
  const cardStyles = {
    fontSize: fontSize === 'large' ? '1.125rem' : 
              fontSize === 'xlarge' ? '1.25rem' : '1rem',
    backgroundColor: highContrast ? '#1a1a1a' : 'white',
    color: highContrast ? '#ffffff' : '#1a1a1a',
    border: highContrast ? '2px solid #ffffff' : '1px solid #e5e7eb',
  };

  return (
    <div className="result-card" style={cardStyles}>
      <div className="result-card-header">
        <div className="result-card-title">
          <h3 className="result-name">{result.nombre}</h3>
          {result.tipo && (
            <span className={`result-type type-${result.tipo}`}>
              {result.tipo}
            </span>
          )}
        </div>
        
        <div className="result-card-actions">
          {!screenReader && (
            <button
              onClick={handleReadAloud}
              className="action-button voice-button"
              aria-label="Escuchar información"
            >
              🔊
            </button>
          )}
          
          <button
            onClick={handleToggleExpand}
            className="action-button expand-button"
            aria-label={isExpanded ? 'Contraer información' : 'Expandir información'}
          >
            {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
        </div>
      </div>

      <div className="result-card-info">
        <div className="info-row">
          <Building2 size={16} aria-hidden="true" />
          <span className="info-text">
            {result.sede}
            {result.edificio && ` - ${result.edificio}`}
          </span>
        </div>

        {result.piso && (
          <div className="info-row">
            <MapPin size={16} aria-hidden="true" />
            <span className="info-text">Piso {result.piso}</span>
            {result.oficina && <span className="info-text"> - {result.oficina}</span>}
          </div>
        )}

        {result.horario && (
          <div className="info-row">
            <Clock size={16} aria-hidden="true" />
            <span className="info-text">{result.horario}</span>
          </div>
        )}

        {result.es_accesible && (
          <div className="info-row accessible">
            <Accessibility size={16} aria-hidden="true" />
            <span className="info-text">Accesible</span>
          </div>
        )}
      </div>

      {isExpanded && (
        <div className="result-card-expanded">
          {result.descripcion && (
            <div className="expanded-section">
              <h4>Descripción</h4>
              <p>{result.descripcion}</p>
            </div>
          )}

          {result.telefono && (
            <div className="expanded-section">
              <h4>Contacto</h4>
              <div className="contact-row">
                <Phone size={16} aria-hidden="true" />
                <a href={`tel:${result.telefono}`}>{result.telefono}</a>
              </div>
              {result.correo && (
                <div className="contact-row">
                  <Mail size={16} aria-hidden="true" />
                  <a href={`mailto:${result.correo}`}>{result.correo}</a>
                </div>
              )}
            </div>
          )}

          {result.servicios && result.servicios.length > 0 && (
            <div className="expanded-section">
              <h4>Servicios disponibles</h4>
              <ul className="servicios-list">
                {result.servicios.map((servicio, index) => (
                  <li key={index}>{servicio}</li>
                ))}
              </ul>
            </div>
          )}

          {result.accesibilidad && (
            <div className="expanded-section">
              <AccessibilityInfo accesibilidad={result.accesibilidad} />
            </div>
          )}

          <div className="result-card-actions-bottom">
            <MapButton 
              address={result.direccion}
              coordinates={result.coordenadas}
              label={`Abrir ruta a ${result.nombre}`}
            />
            
            {result.requisitos && (
              <button className="action-button requisitos-button">
                Ver requisitos
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
5.3 Hook de Voz
tsx
// frontend/src/hooks/useVoice.ts
import { useState, useCallback, useEffect, useRef } from 'react';

interface UseVoiceReturn {
  isListening: boolean;
  transcript: string;
  error: string | null;
  startListening: () => Promise<void>;
  stopListening: () => Promise<void>;
  isSupported: boolean;
}

export const useVoice = (): UseVoiceReturn => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const [isSupported, setIsSupported] = useState(true);

  // Verificar soporte
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSupported(false);
      setError('El reconocimiento de voz no está disponible en este navegador.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'es-PE';
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      const last = event.results.length - 1;
      const result = event.results[last];
      const text = result[0].transcript;
      
      if (result.isFinal) {
        setTranscript(text);
        setIsListening(false);
      } else {
        // Resultados intermedios
        setTranscript(text);
      }
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      
      const errorMessages: Record<string, string> = {
        'not-allowed': 'Permiso de micrófono denegado. Por favor, permite el acceso al micrófono.',
        'audio-capture': 'No se pudo acceder al micrófono. Verifica que esté conectado.',
        'network': 'Error de red. Verifica tu conexión a internet.',
        'language-not-supported': 'El idioma español no está soportado en este navegador.',
        'no-speech': 'No se detectó voz. Por favor, intenta de nuevo.'
      };
      
      setError(errorMessages[event.error] || `Error: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  const startListening = useCallback(async () => {
    if (!recognitionRef.current) {
      setError('Reconocimiento de voz no disponible');
      return;
    }

    try {
      setError(null);
      setTranscript('');
      await recognitionRef.current.start();
      setIsListening(true);
    } catch (err) {
      console.error('Error starting speech recognition:', err);
      setError('No se pudo iniciar el reconocimiento de voz');
      setIsListening(false);
    }
  }, []);

  const stopListening = useCallback(async () => {
    if (recognitionRef.current && isListening) {
      try {
        recognitionRef.current.stop();
        setIsListening(false);
      } catch (err) {
        console.error('Error stopping speech recognition:', err);
      }
    }
  }, [isListening]);

  return {
    isListening,
    transcript,
    error,
    startListening,
    stopListening,
    isSupported,
  };
};
═══════════════════════════════════════════════════════════════
6. DATOS DE EJEMPLO (Seed Data)
═══════════════════════════════════════════════════════════════
python
# backend/scripts/seed_data.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

from app.models.base import Base
from app.models.sede import Sede
from app.models.edificio import Edificio
from app.models.dependencia import Dependencia
from app.models.servicio import Servicio
from app.models.alias import Alias
from app.models.ruta import Ruta
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.core.database import engine, SessionLocal

def seed_database():
    """Carga datos de ejemplo para JUSTICIA ORIENTA"""
    db = SessionLocal()
    
    try:
        # 1. Crear roles
        roles = [
            Rol(nombre="admin", descripcion="Administrador del sistema"),
            Rol(nombre="gestor", descripcion="Gestor de contenido"),
            Rol(nombre="validador", descripcion="Validador de información"),
            Rol(nombre="auditor", descripcion="Auditor de cambios")
        ]
        for rol in roles:
            db.add(rol)
        db.commit()
        
        # 2. Crear sedes
        sede_alzamora = Sede(
            nombre="Sede Alzamora Valdez",
            nombre_corto="Alzamora Valdez",
            direccion="Av. Abancay s/n, esquina con Nicolás de Piérola, Cercado de Lima",
            referencia="Frente al Congreso de la República, junto al Palacio de Justicia",
            latitud=-12.0453,
            longitud=-77.0242,
            horario_atencion="Lunes a viernes de 8:00 am a 4:30 pm",
            telefono="410-1818",
            email="info@cortejusticia.gob.pe",
            tiene_rampas=True,
            tiene_ascensor=True,
            tiene_banios_accesibles=True,
            tiene_estacionamiento=False,
            tiene_personal_asistencia=True,
            estado="activo"
        )
        db.add(sede_alzamora)
        db.commit()
        
        # 3. Crear edificios
        edificio_principal = Edificio(
            sede_id=sede_alzamora.id,
            nombre="Edificio Principal",
            direccion="Av. Abancay s/n",
            numero_pisos=11,
            informacion="Edificio principal de la Corte Superior de Justicia de Lima",
            estado="activo"
        )
        db.add(edificio_principal)
        db.commit()
        
        # 4. Crear dependencias
        dependencias = [
            Dependencia(
                nombre="11.º Juzgado Civil",
                nombre_normalizado="11 juzgado civil",
                tipo="jurisdiccional",
                categoria="juzgado",
                subcategoria="civil",
                sede_id=sede_alzamora.id,
                edificio_id=edificio_principal.id,
                piso="5",
                oficina="503",
                horario_atencion="Lunes a viernes de 8:00 am a 4:00 pm",
                descripcion="Juzgado especializado en materia civil",
                servicios_ofrecidos="Audiencias, notificaciones, presentación de escritos",
                es_accesible=True,
                tiene_rampa=True,
                tiene_ascensor=True,
                estado="activo",
                es_visible_publico=True
            ),
            Dependencia(
                nombre="Recursos Humanos",
                nombre_normalizado="recursos humanos",
                tipo="administrativa",
                categoria="unidad",
                subcategoria="administracion",
                sede_id=sede_alzamora.id,
                edificio_id=edificio_principal.id,
                piso="3",
                oficina="302",
                horario_atencion="Lunes a viernes de 8:30 am a 4:30 pm",
                descripcion="Unidad de Recursos Humanos",
                servicios_ofrecidos="Trámites de personal, contrataciones, permisos, licencias",
                es_accesible=True,
                tiene_rampa=True,
                tiene_ascensor=True,
                estado="activo",
                es_visible_publico=True
            ),
            Dependencia(
                nombre="Coordinación de Informática",
                nombre_normalizado="coordinacion de informatica",
                tipo="administrativa",
                categoria="coordinacion",
                subcategoria="soporte_tecnico",
                sede_id=sede_alzamora.id,
                edificio_id=edificio_principal.id,
                piso="4",
                oficina="402",
                horario_atencion="Lunes a viernes de 8:00 am a 5:00 pm",
                descripcion="Soporte técnico y sistemas informáticos de la Corte",
                servicios_ofrecidos="Soporte de hardware y software, administración de sistemas, redes",
                es_accesible=True,
                tiene_rampa=True,
                tiene_ascensor=True,
                estado="activo",
                es_visible_publico=True
            ),
            Dependencia(
                nombre="Mesa de Partes",
                nombre_normalizado="mesa de partes",
                tipo="servicio",
                categoria="servicio_judicial",
                subcategoria="atencion_ciudadano",
                sede_id=sede_alzamora.id,
                edificio_id=edificio_principal.id,
                piso="1",
                oficina="101",
                horario_atencion="Lunes a viernes de 8:00 am a 4:30 pm",
                descripcion="Recepción de documentos y escritos judiciales",
                servicios_ofrecidos="Presentación de escritos, recepción de documentos, orientación",
                es_accesible=True,
                tiene_rampa=True,
                tiene_ascensor=True,
                estado="activo",
                es_visible_publico=True
            )
        ]
        
        for dep in dependencias:
            db.add(dep)
        db.commit()
        
        # 5. Crear alias
        alias_data = [
            {"dependencia": "11.º Juzgado Civil", "alias": "11 civil", "tipo": "abreviatura"},
            {"dependencia": "11.º Juzgado Civil", "alias": "onceavo civil", "tipo": "coloquial"},
            {"dependencia": "11.º Juzgado Civil", "alias": "juzgado 11", "tipo": "abreviatura"},
            {"dependencia": "11.º Juzgado Civil", "alias": "once civil", "tipo": "coloquial"},
            {"dependencia": "Recursos Humanos", "alias": "rrhh", "tipo": "abreviatura"},
            {"dependencia": "Recursos Humanos", "alias": "recursos", "tipo": "abreviatura"},
            {"dependencia": "Recursos Humanos", "alias": "personal", "tipo": "coloquial"},
            {"dependencia": "Coordinación de Informática", "alias": "informatica", "tipo": "abreviatura"},
            {"dependencia": "Coordinación de Informática", "alias": "soporte", "tipo": "coloquial"},
            {"dependencia": "Coordinación de Informática", "alias": "sistemas", "tipo": "coloquial"},
            {"dependencia": "Mesa de Partes", "alias": "mesa", "tipo": "abreviatura"},
            {"dependencia": "Mesa de Partes", "alias": "partes", "tipo": "abreviatura"},
        ]
        
        for alias_item in alias_data:
            dep = db.query(Dependencia).filter(
                Dependencia.nombre == alias_item["dependencia"]
            ).first()
            if dep:
                alias = Alias(
                    dependencia_id=dep.id,
                    alias=alias_item["alias"],
                    tipo=alias_item["tipo"],
                    prioridad=1,
                    estado="activo"
                )
                db.add(alias)
        db.commit()
        
        # 6. Crear rutas
        ruta_1 = Ruta(
            origen="Ingreso principal",
            destino_id=db.query(Dependencia).filter_by(nombre="11.º Juzgado Civil").first().id,
            instrucciones="Desde el ingreso principal, dirígete a los ascensores, selecciona el quinto piso, gira a la derecha y avanza hasta la oficina 503",
            tipo="peatonal",
            distancia_aproximada="50 metros",
            tiempo_aproximado="2 minutos",
            nivel_dificultad="baja",
            es_accesible=True,
            estado="activo"
        )
        db.add(ruta_1)
        db.commit()
        
        print("✅ Datos de ejemplo cargados correctamente")
        
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
═══════════════════════════════════════════════════════════════
7. INSTRUCCIONES DE INSTALACIÓN
═══════════════════════════════════════════════════════════════
bash
# INSTALACIÓN DE JUSTICIA ORIENTA

# ═══════════════════════════════════════════════════════
# 1. REQUISITOS PREVIOS
# ═══════════════════════════════════════════════════════
# - Ubuntu 22.04 LTS o superior
# - Python 3.11+
# - Node.js 18+
# - PostgreSQL 15+
# - Git

# ═══════════════════════════════════════════════════════
# 2. CLONAR REPOSITORIO
# ═══════════════════════════════════════════════════════
git clone https://github.com/corte-justicia/justicia-orienta.git
cd justicia-orienta

# ═══════════════════════════════════════════════════════
# 3. CONFIGURAR BASE DE DATOS
# ═══════════════════════════════════════════════════════
sudo -u postgres psql

# Crear usuario y base de datos
CREATE USER justicia_user WITH PASSWORD 'segura_password';
CREATE DATABASE justicia_orienta OWNER justicia_user;
GRANT ALL PRIVILEGES ON DATABASE justicia_orienta TO justicia_user;

# Habilitar extensión pg_trgm para búsqueda fuzzy
\c justicia_orienta
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\q

# ═══════════════════════════════════════════════════════
# 4. INSTALAR BACKEND
# ═══════════════════════════════════════════════════════
cd backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements/prod.txt

# Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con los valores correctos

# Ejecutar migraciones
alembic upgrade head

# Cargar datos de ejemplo
python scripts/seed_data.py

# Iniciar servidor
uvicorn app.main:app --host 0.0.0.0 --port 8000

# ═══════════════════════════════════════════════════════
# 5. INSTALAR FRONTEND
# ═══════════════════════════════════════════════════════
# En otra terminal
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con VITE_API_URL=http://localhost:8000

# Iniciar en modo desarrollo
npm run dev

# Construir para producción
npm run build

# ═══════════════════════════════════════════════════════
# 6. CONFIGURAR NGINX (Producción)
# ═══════════════════════════════════════════════════════
sudo nano /etc/nginx/sites-available/justicia-orienta

# Configuración:
server {
    listen 80;
    server_name orienta.cortejusticia.gob.pe;
    
    location / {
        root /var/www/justicia-orienta/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/justicia-orienta /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# ═══════════════════════════════════════════════════════
# 7. VERIFICAR INSTALACIÓN
# ═══════════════════════════════════════════════════════
# Backend: curl http://localhost:8000/health
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/api/docs

echo "✅ JUSTICIA ORIENTA instalado correctamente"
═══════════════════════════════════════════════════════════════
8. REQUISITOS DE PRODUCCIÓN
═══════════════════════════════════════════════════════════════
txt
# backend/requirements/prod.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
python-dotenv==1.0.0
httpx==0.25.1
cryptography==41.0.7
email-validator==2.1.0
# Opcional
# sentry-sdk==1.38.0
json
// frontend/package.json
{
  "name": "justicia-orienta",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "lucide-react": "^0.294.0",
    "react-hook-form": "^7.48.2",
    "@hookform/resolvers": "^3.3.2",
    "zod": "^3.22.4",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.1.0",
    "class-variance-authority": "^0.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.53.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.4",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.2.2",
    "vite": "^5.0.0"
  }
}
═══════════════════════════════════════════════════════════════
9. PRUEBAS
═══════════════════════════════════════════════════════════════
python
# backend/tests/test_api/test_busqueda.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_buscar_dependencia():
    """Prueba búsqueda de dependencia por nombre"""
    response = client.post(
        "/api/v1/search/buscar",
        json={"query": "11 juzgado civil"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["resultados"]) > 0
    assert "11.º Juzgado Civil" in str(data["resultados"])

def test_buscar_por_alias():
    """Prueba búsqueda usando alias"""
    response = client.post(
        "/api/v1/search/buscar",
        json={"query": "rrhh"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["resultados"]) > 0
    assert "Recursos Humanos" in str(data["resultados"])

def test_busqueda_fallback():
    """Prueba búsqueda sin resultados (fallback seguro)"""
    response = client.post(
        "/api/v1/search/buscar",
        json={"query": "xyz123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] == True
    assert data["sugerencia"] is not None

def test_sugerencias():
    """Prueba autocompletado de sugerencias"""
    response = client.get(
        "/api/v1/search/sugerencias?q=11"
    )
    assert response.status_code == 200
    data = response.json()
    assert "sugerencias" in data
═══════════════════════════════════════════════════════════════
10. CHECKLIST DE IMPLEMENTACIÓN
═══════════════════════════════════════════════════════════════
markdown
## ✅ Checklist de Implementación

### FASE 1: INFRAESTRUCTURA
- [ ] Servidor Linux configurado
- [ ] PostgreSQL 15 instalado y configurado
- [ ] Nginx instalado
- [ ] SSL Let's Encrypt configurado
- [ ] Backups automatizados

### FASE 2: BACKEND
- [ ] Proyecto FastAPI creado
- [ ] Modelos de datos implementados (8 tablas)
- [ ] Migraciones ejecutadas
- [ ] API Endpoints implementados (15+)
- [ ] Servicio de interpretación implementado
- [ ] Servicio de búsqueda implementado
- [ ] Autenticación JWT implementada
- [ ] Panel de administración (API)
- [ ] Auditoría implementada
- [ ] Pruebas unitarias (80%+ cobertura)

### FASE 3: FRONTEND
- [ ] Proyecto React + TypeScript creado
- [ ] Componente SearchBar implementado
- [ ] Componente ResultCard implementado
- [ ] Modo voz implementado (Web Speech API)
- [ ] Modo accesible implementado
- [ ] Panel de administración implementado
- [ ] Dashboard de métricas implementado
- [ ] Responsive Design implementado
- [ ] PWA (opcional)

### FASE 4: DATOS
- [ ] Datos de ejemplo cargados
- [ ] 3+ sedes configuradas
- [ ] 20+ dependencias configuradas
- [ ] 30+ alias configurados
- [ ] Servicios configurados por dependencia
- [ ] Rutas configuradas

### FASE 5: PRUEBAS
- [ ] Pruebas de búsqueda
- [ ] Pruebas de interpretación
- [ ] Pruebas de accesibilidad (Lighthouse)
- [ ] Pruebas con usuarios reales
- [ ] Pruebas con adultos mayores
- [ ] Pruebas con personas con discapacidad

### FASE 6: DEPLOYMENT
- [ ] Código en repositorio
- [ ] CI/CD configurado
- [ ] Backup configurado
- [ ] Monitoreo configurado
- [ ] Documentación completa
- [ ] Manual de usuario
- [ ] Manual de administrador

### FASE 7: LANZAMIENTO
- [ ] Capacitación al personal
- [ ] Campaña de difusión
- [ ] QR generados e instalados
- [ ] Piloto con usuarios reales
- [ ] Métricas recolectadas
- [ ] Iteración y mejora
═══════════════════════════════════════════════════════════════
11. ENTREGABLES FINALES
═══════════════════════════════════════════════════════════════
Al finalizar la implementación, se deben entregar:

Código fuente completo (backend + frontend)

Base de datos (estructura + datos de ejemplo)

Documentación API (OpenAPI/Swagger)

Manual de usuario (PDF/Markdown)

Manual de administrador (PDF/Markdown)

Guía de despliegue (PDF/Markdown)

Video demostrativo (5-10 minutos)

Presentación (para el concurso)

Scripts de instalación (automatizados)

Reporte de pruebas (accesibilidad, usabilidad)

═══════════════════════════════════════════════════════════════
12. RECOMENDACIONES ADICIONALES PARA LA IA O INGENIERO
═══════════════════════════════════════════════════════════════
Empieza con el MVP: No intentes implementar todo de una vez. Prioriza:

Búsqueda básica (exacta)

Resultados con ubicación

Modo accesible básico

Panel administrativo simple

Usa iteraciones cortas: Sprint de 1-2 semanas, entrega funcionalidad incremental.

Prueba con usuarios reales: Involucra a personal de la Corte y ciudadanos desde el inicio.

Documenta TODO: El proyecto debe ser mantenible por otras personas.

Piensa en escalabilidad: Diseña para 100+ dependencias y 10+ sedes.

Accesibilidad como requisito: Usa herramientas como axe, Lighthouse, WAVE.

Seguridad desde el día 1: HTTPS, validación de inputs, protección de datos.

Métricas: Implementa desde el principio el registro de métricas.

Copias de seguridad: Configura backups automáticos de la base de datos.

Capacitación: Prepara material de capacitación para el personal.

═══════════════════════════════════════════════════════════════
FIN DEL PROMPT DE IMPLEMENTACIÓN
═══════════════════════════════════════════════════════════════
PROYECTO: JUSTICIA ORIENTA v1.0
FECHA: 2026-08-17
VERSIÓN: 1.0
AUTOR: Equipo de Desarrollo

"La tecnología es el medio, el ciudadano es el fin."

Entregar código funcional que pueda ser desplegado en la infraestructura de la Corte Superior de Justicia de Lima.

text

---

# 📋 RESUMEN DEL PROMPT

| Aspecto | Contenido |
|---------|-----------|
| **Arquitectura** | Full-stack: React + FastAPI + PostgreSQL |
| **Modelos de datos** | 10 tablas completas (SQLAlchemy) |
| **APIs** | 15+ endpoints documentados |
| **Componentes Frontend** | SearchBar, ResultCard, VoiceInput, Admin Panel |
| **Lógica de negocio** | Interpretación de lenguaje natural, búsqueda fuzzy (pg_trgm) |
| **Accesibilidad** | Modo voz, alto contraste, lectores de pantalla, navegación por teclado |
| **Datos de ejemplo** | Sedes, dependencias, alias, rutas (seed_data.py) |
| **Instalación** | Scripts completos (bash, Python) |
| **Pruebas** | Tests unitarios y de integración |
| **Checklist** | 7 fases, 50+ items de implementación |
| **Entregables** | 10 documentos y artefactos |

---

**Este prompt permite que cualquier IA o ingeniero de software tenga todo lo necesario para implementar JUSTICIA ORIENTA desde cero.**
