# Justicia Orienta

Orientador ciudadano accesible para la Corte Superior de Justicia de Lima — buena práctica postulada al
Concurso "Gestores de Atención al Ciudadano" (ODANC Lima, 2026).

Toda la tecnología usada en este repositorio es de código abierto y sin costo de licencia: Python,
FastAPI, SQLAlchemy, SQLite/PostgreSQL, HTML/CSS/JS nativos.

## Qué hay en esta carpeta

| Archivo / carpeta | Qué es |
|---|---|
| `Presentación y Bases del Concurso...pdf` | Bases oficiales del concurso (ODANC Lima). |
| `SUPER_MEGA_PROMPT_JUSTICIA_ORIENTA_2.0.md` | Visión completa original del proyecto. |
| `JusticiaOrienta_00_Diseno_Servicio.html` | Brief de diseño de servicio: matriz de ideas, ficha de buena práctica, principios de accesibilidad. Ábrelo con doble clic. |
| `JusticiaOrienta_01_Propuesta_Anonima.docx` | **Cuerpo oficial del concurso** — A4, Arial 12, doble espacio, sin nombres de autores. |
| `JusticiaOrienta_02_Etiqueta_Sobre.docx` | Etiqueta con título y seudónimo para el sobre cerrado. |
| `JusticiaOrienta_03_Hoja_Identificacion.docx` | Único ejemplar no anónimo: nombres, correo y firmas. |
| `JusticiaOrienta_04_Plantilla_Catalogo_Piloto.xlsx` | Plantilla para el levantamiento real del catálogo (dependencias, horarios, accesibilidad). |
| `JusticiaOrienta_05_Nota_Interna_para_Firma.docx` | Nota de una página para conseguir la autorización y firma del responsable. |
| `prototipo-v1/` | **V1** — micrositio estático de un solo archivo, sin backend, para demostrar el concepto sin instalar nada. |
| `app/` | **V2** — aplicación real: backend FastAPI + base de datos + panel de administración. Esto es lo que sigue creciendo. |

## Cómo correr la aplicación real (`app/`)

Requiere Python 3.10+ (ya viene con `pip`, no hace falta nada más para empezar).

```bash
pip install -r requirements.txt

# 1. Crea el usuario administrador inicial
python -m app.seed

# 2. Carga el catálogo desde el Excel de levantamiento (real o de ejemplo)
python -m app.import_excel "JusticiaOrienta_04_Plantilla_Catalogo_Piloto.xlsx"

# 3. Levanta el servidor
python -m uvicorn app.main:app --reload
```

Luego abre:

- **http://127.0.0.1:8000/** — el micrositio público (lo que ve el ciudadano).
- **http://127.0.0.1:8000/admin** — el panel de administración (lo que usa cada área para mantener su información).
  - Usuario inicial: `admin@justiciaorienta.local` / contraseña impresa por `app.seed` — **cámbiala de inmediato**.
- **http://127.0.0.1:8000/api/docs** — documentación interactiva de la API (generada automáticamente por FastAPI).

### Flujo de trabajo pensado para las áreas

1. Cada área llena o corrige su parte del Excel de levantamiento (`JusticiaOrienta_04...xlsx`).
2. Informática corre `python -m app.import_excel` para volcar esos cambios a la base de datos, **o** cada
   gestor de área edita directamente desde `/admin` (solo ve y edita las dependencias de su propia área).
3. El micrositio público (`/`) refleja los cambios de inmediato — solo muestra dependencias en estado
   `activo`, para que nada salga a producción sin haber sido validado.
4. Todo cambio queda registrado en `/api/admin/auditoria` (quién, cuándo, qué campo cambió).

### Producción vs. desarrollo

Por defecto la app usa SQLite (`justicia_orienta.db`, cero instalación). Para producción, define la
variable de entorno `DATABASE_URL` apuntando a PostgreSQL — no hay que tocar código:

```
DATABASE_URL=postgresql+psycopg2://usuario:clave@host:5432/justicia_orienta
```

Copia `.env.example` a `.env` y ajusta los valores (incluida `JUSTICIA_ORIENTA_SECRET`, que firma las
sesiones — cámbiala antes de cualquier uso real).

**Limitación conocida, honesta:** todavía no hay migraciones versionadas (Alembic); las tablas se crean
automáticamente al iniciar. Es suficiente para el piloto; es la siguiente mejora recomendada antes de un
despliegue institucional definitivo.

## Hoja de ruta (de dónde venimos, hacia dónde va)

| Fase | Qué es | Estado |
|---|---|---|
| V0 | Protocolo humano + catálogo en papel/Excel | Diseñado (ficha de buena práctica) |
| V1 | Micrositio estático, sin backend | Hecho — `prototipo-v1/` |
| **V2** | **Backend real + base de datos + panel de administración con roles** | **Hecho — `app/`, esto es lo que estás viendo** |
| V3 | Asistente de interpretación de lenguaje natural sobre el catálogo validado | No iniciado |
| V4 | Navegación interior avanzada, integraciones adicionales | No iniciado |

## Principios que no se negocian

- **Nunca inventar información institucional.** Si el buscador no tiene certeza, deriva a atención humana
  en vez de adivinar (ver el mensaje de respaldo en `/api/buscar`).
- **Cada área es dueña de su información.** Un/a gestor/a de área solo puede editar dependencias de su
  propia área; Informática administra la plataforma, no el contenido.
- **Accesibilidad no es una fase futura.** Alto contraste, texto ampliable y lectura en voz alta están en
  el V1 y el V2, no reservados para una versión posterior.
