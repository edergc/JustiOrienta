# Justicia Orienta — Guía de despliegue

Orientador ciudadano accesible para la Corte Superior de Justicia de Lima: sitio público de búsqueda
en lenguaje natural + panel administrativo por roles, servidos por un único backend FastAPI + PostgreSQL.

Esta guía está pensada para que **otro profesional de Informática, sin conocimiento previo del
proyecto**, pueda clonar el repositorio, configurar la base de datos, levantar la aplicación en un
servidor y verificar que todo funciona correctamente (probarlo de punta a punta).

Toda la tecnología es de código abierto y sin costo de licencia: Python, FastAPI, SQLAlchemy,
PostgreSQL, HTML/CSS/JS nativos (sin frameworks de frontend, sin Node.js, sin Docker obligatorio).

**Repositorio:** https://github.com/edergc/JustiOrienta

```bash
git clone https://github.com/edergc/JustiOrienta.git
cd JustiOrienta
```

## Índice

1. [Requisitos](#1-requisitos)
2. [Arquitectura (qué se está desplegando)](#2-arquitectura-qué-se-está-desplegando)
3. [Instalación rápida para pruebas (SQLite)](#3-instalación-rápida-para-pruebas-sqlite)
4. [Instalación recomendada con PostgreSQL](#4-instalación-recomendada-con-postgresql)
5. [Configuración de `.env`](#5-configuración-de-env)
6. [Crear y preparar la base de datos](#6-crear-y-preparar-la-base-de-datos)
7. [Ejecutar migraciones](#7-ejecutar-migraciones)
8. [Crear administrador inicial](#8-crear-administrador-inicial)
9. [Cargar el catálogo institucional](#9-cargar-el-catálogo-institucional)
10. [Ejecutar la aplicación](#10-ejecutar-la-aplicación)
11. [Acceso desde otra PC de la LAN](#11-acceso-desde-otra-pc-de-la-lan)
12. [Crear un servicio en Windows Server](#12-crear-un-servicio-en-windows-server)
13. [Pruebas automatizadas](#13-pruebas-automatizadas)
14. [Prueba funcional completa (checklist)](#14-prueba-funcional-completa-checklist)
15. [Roles (para poder probar el flujo editorial)](#15-roles-para-poder-probar-el-flujo-editorial)
16. [Migraciones futuras](#16-migraciones-futuras)
17. [Respaldos y restauración](#17-respaldos-y-restauración)
18. [Logs y diagnóstico](#18-logs-y-diagnóstico)
19. [Despliegue alternativo: Render (opcional)](#19-despliegue-alternativo-render-opcional)
20. [Seguridad](#20-seguridad)
21. [Estructura del repositorio](#21-estructura-del-repositorio)
22. [De dónde salen los datos reales](#22-de-dónde-salen-los-datos-reales)
23. [Integración continua (CI)](#23-integración-continua-ci)
24. [Solución de problemas](#24-solución-de-problemas)
25. [Checklist final de instalación](#25-checklist-final-de-instalación)

---

## 1. Requisitos

**Obligatorio:**

- Git
- Python 3.10 o superior (con `pip`)
- PostgreSQL, para la instalación recomendada / producción
- Cliente de PostgreSQL (`psql`, `pg_dump`, `pg_restore`) para administración y respaldos

**No hace falta instalar:** Node.js, npm, React, Vite, Docker, Redis, ni ningún servicio de IA externo.
Todas las dependencias Python reales están en `requirements.txt` (verificado contra cada `import` del
código: no falta ni sobra nada).

## 2. Arquitectura (qué se está desplegando)

Es un **monolito sencillo de desplegar**: un solo proceso Python sirve el sitio público, el panel
administrativo y la API, todos desde el mismo puerto. No hay un frontend separado que compilar ni
sincronizar con el backend.

```
                    Navegador (ciudadano / panel admin)
                                  │
                            HTTP(S) : 8743
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │      app/main.py        │
                    │  FastAPI + Uvicorn       │
                    │  sitio público + /admin  │
                    │  + API (/api/v1)         │
                    └────────────┬─────────────┘
                                 │
                     routers/ → crud/ → models/
                                 │
                            TCP : 5432
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       PostgreSQL         │
                    │      justicia_orienta    │
                    └─────────────────────────┘
```

## 3. Instalación rápida para pruebas (SQLite)

Para probar el sistema en minutos, sin instalar PostgreSQL (usa SQLite, ya preconfigurado en
`.env.example` como resguardo de cero instalación).

```bash
git clone https://github.com/edergc/JustiOrienta.git
cd JustiOrienta
```

**Entorno virtual:**

```powershell
# Windows PowerShell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
# Si PowerShell bloquea la activación:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

**Instalar dependencias y preparar el entorno:**

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env          # Windows: Copy-Item .env.example .env
```

Para esta prueba rápida, `.env` puede quedar tal cual (`DATABASE_URL=sqlite:///./justicia_orienta.db`).

**Crear el esquema, el administrador y cargar datos de prueba:**

```bash
python -m alembic upgrade head
python -m app.seed
python -m app.cargar_directorio_pj
```

**Levantar el servidor:**

```bash
python run.py
```

Abrir:

- http://127.0.0.1:8743/ — sitio público
- http://127.0.0.1:8743/admin — panel de administración
- http://127.0.0.1:8743/api/docs — documentación interactiva de la API

## 4. Instalación recomendada con PostgreSQL

Para un servidor institucional o producción, usar PostgreSQL (no SQLite). La aplicación soporta ambos
motores sin tocar código, vía `DATABASE_URL` -- el entorno real de este proyecto corre sobre Postgres.

PostgreSQL puede estar:

1. En el mismo servidor que la aplicación.
2. En un servidor de base de datos separado.
3. En una instancia administrada compatible con PostgreSQL (Neon, RDS, Cloud SQL, etc.).

## 5. Configuración de `.env`

```bash
cp .env.example .env          # Windows: Copy-Item .env.example .env
```

`.env.example` define todas las variables reales que lee `app/config.py`: `ENTORNO`, `DATABASE_URL`,
`JUSTICIA_ORIENTA_SECRET`, `URL_PUBLICA` y las variables `SMTP_*` (correo de "olvidé mi contraseña" --
si se dejan vacías, el correo no se envía de verdad, solo queda en el log, para poder probar el flujo
sin credenciales reales).

**Desarrollo con PostgreSQL:**

```env
ENTORNO=desarrollo
DATABASE_URL=postgresql+psycopg2://justicia_app:CLAVE@localhost:5432/justicia_orienta
JUSTICIA_ORIENTA_SECRET=cambia-esta-clave-por-una-larga-y-aleatoria
URL_PUBLICA=http://localhost:8743
```

**Producción:**

```env
ENTORNO=produccion
DATABASE_URL=postgresql+psycopg2://justicia_app:CLAVE@SERVIDOR_POSTGRES:5432/justicia_orienta
JUSTICIA_ORIENTA_SECRET=secreto-unico-y-distinto-al-de-desarrollo
URL_PUBLICA=https://dominio.institucional.gob.pe
```

`.env` nunca se sube al repositorio (está en `.gitignore`) -- cada máquina necesita el suyo. Si
`ENTORNO=produccion` y `JUSTICIA_ORIENTA_SECRET` sigue con el valor de relleno de `.env.example`, el
servidor **se niega a arrancar** en vez de correr con una clave que cualquiera que lea el repositorio
público podría usar para forjar un token de administrador -- ver la sección de Seguridad.

## 6. Crear y preparar la base de datos

**PostgreSQL instalado localmente:**

```bash
psql -U postgres
```

```sql
CREATE USER justicia_app WITH PASSWORD 'CAMBIAR_ESTA_CLAVE';
CREATE DATABASE justicia_orienta OWNER justicia_app;
\q
```

**Probar la conexión:**

```bash
psql -h localhost -U justicia_app -d justicia_orienta
```

Si pide la contraseña y entra mostrando `justicia_orienta=>`, la conexión funciona (`\q` para salir).

**Si PostgreSQL está en otro servidor**, por ejemplo:

```
Servidor de la aplicación: 172.20.1.51
Servidor PostgreSQL:       172.20.1.52 : 5432
Base de datos:             justicia_orienta
Usuario:                   justicia_app
```

el `.env` queda:

```env
DATABASE_URL=postgresql+psycopg2://justicia_app:CLAVE@172.20.1.52:5432/justicia_orienta
```

Además, el administrador de PostgreSQL debe permitir la conexión desde el servidor de la aplicación en
`pg_hba.conf`, PostgreSQL debe escuchar en la interfaz correcta (`postgresql.conf`), y debe existir
conectividad TCP al puerto 5432 entre ambos servidores.

## 7. Ejecutar migraciones

Con `DATABASE_URL` ya configurada:

```bash
python -m alembic upgrade head
```

Esto crea (o actualiza) la estructura de tablas. **Nunca crear tablas a mano** -- la estructura la
administra Alembic (`migrations/versions/`), siempre.

Verificar:

```bash
alembic current
```

o directamente en PostgreSQL:

```sql
\dt
```

## 8. Crear administrador inicial

```bash
python -m app.seed
```

Crea el usuario administrador inicial e imprime su contraseña temporal. Al entrar por primera vez a
`/admin` (DNI `12345678`), el sistema **exige** cambiarla -- no es solo una sugerencia: el backend
rechaza cualquier otro endpoint con 403 mientras eso no pase. El acceso es por DNI (8 dígitos), no por
correo, y la cuenta se bloquea 15 minutos después de 5 intentos fallidos seguidos.

## 9. Cargar el catálogo institucional

**Opción A -- directorio oficial** (recomendada, ya incluido en el repositorio):

```bash
python -m app.cargar_directorio_pj
```

Extrae del PDF oficial (`fuentes/Directorio_CSJLI_oficial_2025-05-08.pdf`) sedes y dependencias reales,
sin duplicar si se vuelve a ejecutar.

**Opción B -- Excel propio:**

```bash
python -m app.import_excel "tu_archivo.xlsx"
```

Con las columnas que espera `app/import_excel.py` (usa "Exportar catálogo" desde `/admin` una vez que
tengas datos, para obtener un archivo con el formato exacto).

**Opción C -- datos ya incluidos en el repositorio**, usados por el proceso de carga que corre en cada
despliegue de producción (ver `render.yaml`):

```bash
python -m app.cargar_directorio_excel        # usa DirectorioCSJLI.xlsx
python -m app.cargar_titulares --sede "Sede Javier Alzamora Valdez"   # usa ConformacionCSJLima.xlsx
python -m app.cargar_mapa_jav_nivel1         # mapa interno de la sede piloto (datos ya incluidos en el script)
```

Cargar datos y publicarlos son cosas distintas: lo cargado queda en `revision` hasta que un(a)
validador(a) del área correspondiente lo apruebe (ver sección de Roles).

## 10. Ejecutar la aplicación

```bash
python run.py
```

- Sitio público: http://127.0.0.1:8743/
- Panel de administración: http://127.0.0.1:8743/admin
- API / Swagger: http://127.0.0.1:8743/api/docs

El puerto (por defecto `8743`) se cambia sin tocar código:

```bash
PORT=9231 python run.py       # PowerShell: $env:PORT=9231; python run.py
```

## 11. Acceso desde otra PC de la LAN

Por defecto el servidor escucha solo en `127.0.0.1`. Para que otros equipos de la red lo vean, debe
escuchar en todas las interfaces:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8743
```

(`run.py` ya expone esto vía la variable de entorno `HOST=0.0.0.0`).

**Identificar la IP del servidor** (Windows: `ipconfig`, ejemplo `172.20.1.51`) y probar desde otro
equipo: `http://172.20.1.51:8743/`.

**Firewall de Windows**, si bloquea el puerto:

```powershell
New-NetFirewallRule -DisplayName "Justicia Orienta - TCP 8743" -Direction Inbound -Protocol TCP -LocalPort 8743 -Action Allow
```

En una red institucional, conviene restringir la regla a las subredes necesarias en vez de abrir el
puerto sin restricción.

## 12. Crear un servicio en Windows Server

Para un servidor institucional no conviene depender de una consola abierta. Antes de convertirlo en
servicio, comprobar manualmente que todo funciona:

```powershell
cd C:\JusticiaOrienta
.\.venv\Scripts\Activate.ps1
python -m alembic upgrade head
python -m app.seed
python run.py
```

Solo cuando esto funciona sin errores, convertirlo en servicio -- por ejemplo con **NSSM** (Non-Sucking
Service Manager) o el mecanismo de servicios que use la institución:

| Parámetro | Valor |
|---|---|
| Programa | `C:\JusticiaOrienta\.venv\Scripts\python.exe` |
| Argumentos | `-m uvicorn app.main:app --host 0.0.0.0 --port 8743` |
| Directorio | `C:\JusticiaOrienta` |
| Variables de entorno | `DATABASE_URL`, `ENTORNO=produccion`, `JUSTICIA_ORIENTA_SECRET` (las de `.env`) |

## 13. Pruebas automatizadas

```bash
python -m pytest
```

158 pruebas (las mismas que corren en GitHub Actions, ver "Integración continua"), contra una base de
datos SQLite en memoria, aislada de la de desarrollo. Cubren autenticación y roles, el flujo de
publicación completo, el buscador y el detector de duplicados, el mapa interno / wayfinding, solicitudes
de atención, sedes/edificios/servicios, indicadores, exportaciones y el directorio en PDF.

```bash
python -m pytest -v                    # con detalle de cada prueba
python -m pytest tests/ -k "buscar"    # solo un subconjunto
```

**Auditoría de accesibilidad estática** sobre el HTML servido (idioma declarado, texto alternativo,
etiquetas de formulario, nombre accesible en botones/enlaces/diálogos):

```bash
python -m app.auditoria_accesibilidad
```

No reemplaza una revisión real con lector de pantalla ni verifica contraste de color (eso necesita
render real), pero deja evidencia objetiva y repetible en cada cambio de plantilla.

## 14. Prueba funcional completa (checklist)

Después de desplegar, recorrer esta lista:

**Técnica**

```
[ ] PostgreSQL responde
[ ] DATABASE_URL funciona
[ ] alembic upgrade head terminó sin errores
[ ] La aplicación inicia
[ ] El puerto configurado responde
[ ] /api/docs responde
[ ] logs/justicia_orienta.log no muestra errores críticos
```

**Ciudadano (sitio público)**

```
[ ] La página principal abre
[ ] El buscador (texto) funciona
[ ] La búsqueda por voz funciona en un navegador compatible
[ ] Un resultado muestra la información esperada
[ ] Lectura en voz alta, alto contraste, texto ampliable y tema oscuro funcionan
[ ] Un código QR de prueba abre la página correcta
[ ] El directorio en PDF puede descargarse
```

**Administración**

```
[ ] /admin abre y el login funciona
[ ] El cambio obligatorio de contraseña en el primer ingreso funciona
[ ] Un usuario gestor puede editar contenido de su propia área
[ ] Un gestor NO puede publicar directamente (queda en revisión)
[ ] Un validador puede aprobar, y lo aprobado aparece en el sitio público
[ ] La pestaña Auditoría registra las acciones anteriores, con IP de origen
```

**Datos**

```
[ ] Crear, editar y aprobar una dependencia
[ ] Crear, desactivar y reactivar un servicio
[ ] Exportar el catálogo a Excel, y reimportarlo
[ ] Generar un código QR
[ ] Descargar el reporte de indicadores
```

## 15. Roles (para poder probar el flujo editorial)

| Rol | Puede |
|---|---|
| **admin** | Todo: sedes, edificios, usuarios, dependencias y servicios de cualquier área; aprobar cualquier cosa. |
| **gestor** | Crear/editar dependencias y servicios solo de su propia área. Nunca publica directamente: queda en `revision`. |
| **validador** | Lo mismo que gestor, más aprobar (`revision` → `activo`) o devolver a revisión contenido de su propia área. |
| **auditor** | Solo lectura de `/admin/auditoria` y de los indicadores. |
| **consulta** | Indicadores, reporte en Excel y auditoría en solo lectura -- sin gestión del catálogo. |

Ningún rol distinto de admin puede autopublicarse ni reasignar contenido a un área ajena, aunque el
payload del formulario lo indique -- el servidor lo valida igual del lado del backend.

## 16. Migraciones futuras

Si se modifica un modelo en `app/models/`, no se toca la estructura de producción a mano:

```bash
python -m alembic revision --autogenerate -m "descripción del cambio"
# revisar el archivo generado en migrations/versions/
python -m alembic upgrade head
```

Flujo recomendado: modificar el modelo → generar la migración → revisarla a mano → `pytest` en local →
commit → en producción, `alembic upgrade head`.

## 17. Respaldos y restauración

**Crear un respaldo** (detecta el motor por `DATABASE_URL`, mismo comando para los dos):

```bash
python backup_db.py
```

En PostgreSQL corre `pg_dump -Fc` (formato comprimido, restaurable con `pg_restore`) hacia `backups/`,
con marca de fecha y hora; los respaldos de más de 30 días se purgan automáticamente (`DIAS_RETENCION`
en `backup_db.py`). En SQLite, copia el archivo `.db`. Requiere que `pg_dump` esté en el `PATH` (viene
con el cliente de PostgreSQL). Es una acción manual y explícita -- no corre sola ni programada; para
automatizarla, se agenda este mismo comando con el Programador de tareas de Windows o `cron`.

**Restaurar un respaldo de PostgreSQL:**

```bash
createdb -U postgres justicia_orienta          # solo si la base de datos todavía no existe
pg_restore -h localhost -U justicia_app -d justicia_orienta backups/justicia_orienta_20260918_113000.dump
python -m alembic upgrade head                 # solo si el código tiene migraciones más nuevas que el respaldo
```

El `.dump` ya trae esquema y datos juntos -- a diferencia de instalar desde cero, acá **no** hace falta
`app.seed` ni cargar el catálogo de nuevo, eso ya viene dentro del respaldo.

**Restaurar un respaldo de SQLite** es copiar el archivo de vuelta:

```bash
cp backups/justicia_orienta_20260918_113000.db justicia_orienta.db
```

Restaurar sobre una base real de producción debe tratarse como una operación controlada: verificar
primero que el destino es realmente la base que se quiere sobrescribir.

## 18. Logs y diagnóstico

Los errores del servidor quedan en `logs/justicia_orienta.log` (rotación automática: 1 MB por archivo,
5 respaldos), además de la consola.

| Síntoma | Qué revisar |
|---|---|
| La app no inicia | Correr `python run.py` directo y leer el error en consola. |
| Falla la conexión a PostgreSQL | `psql -h HOST -U justicia_app -d justicia_orienta`; revisar `pg_hba.conf` / `postgresql.conf` / firewall. |
| Falla `alembic upgrade head` | `alembic current` y `alembic heads`; confirmar que `DATABASE_URL` apunta a la base correcta. |
| El puerto está ocupado (Windows) | `netstat -ano \| findstr :8743`, luego `tasklist /FI "PID eq NUMERO_PID"`. |

## 19. Despliegue alternativo: Render (opcional)

El repositorio incluye `render.yaml` como referencia de despliegue en la nube, con el `startCommand`
completo (migraciones, administrador, carga de datos, arranque). No es la única forma de desplegar --
sirve como documentación de qué pasos hacen falta en cualquier plataforma. Si se usa Render, hay que
crear el Web Service apuntando a este repositorio y configurar como variables de entorno (no en el
repo): `DATABASE_URL`, `JUSTICIA_ORIENTA_SECRET`, `URL_PUBLICA` y, opcionalmente, `SMTP_*`.

## 20. Seguridad

- **Secreto de sesión obligatorio en producción**: con `ENTORNO=produccion`, si `JUSTICIA_ORIENTA_SECRET`
  sigue con el valor de relleno, el servidor se niega a arrancar (`app/main.py`).
- **Contraseñas con bcrypt** y bloqueo de cuenta tras 5 intentos fallidos (15 minutos).
- **Limitador de tasa en memoria** (`app/rate_limit.py`) en "olvidé mi contraseña" y "que me llamen o me
  escriban".
- **Cabeceras HTTP de seguridad** en cada respuesta: `Content-Security-Policy` estricto,
  `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy` y
  `Strict-Transport-Security` (HSTS).
- **Escape de HTML** en todo el contenido de texto libre, y **neutralización de fórmulas** en cada celda
  exportada a Excel (`app/excel_utils.py`).
- **Auditoría con IP de origen** en cada evento de sesión (login OK/fallido, bloqueo, cambio de
  contraseña) y cada exportación; filtrable y exportable desde `/admin` → Auditoría. Ningún rol puede
  editar o borrar un registro de auditoría ya escrito.
- **HTTPS obligatorio antes de exponer el sistema en un dominio público** -- el piloto en LAN/`127.0.0.1`
  corre en HTTP simple; en producción real, ponerlo detrás de un proxy inverso (Caddy, Nginx + Let's
  Encrypt, o el balanceador de la institución) con TLS.

## 21. Estructura del repositorio

```
JustiOrienta/
├── .github/workflows/       Integración continua (pytest en cada push/PR)
├── app/
│   ├── config.py            Configuración centralizada (lee .env)
│   ├── database.py          Motor SQLAlchemy y sesión
│   ├── security.py          Hash de contraseñas, JWT, permisos por rol/área
│   ├── nlp.py                Interpretación de lenguaje natural del buscador
│   ├── main.py               Arma la app, monta routers, cabeceras de seguridad
│   ├── rate_limit.py         Limitador de tasa en memoria
│   ├── rutas_internas.py     Cálculo de ruta más corta (mapa interno)
│   ├── models/               Una tabla por archivo
│   ├── schemas/               Esquemas Pydantic de entrada/salida
│   ├── crud/                 Acceso a datos y reglas de negocio
│   ├── routers/               Endpoints HTTP, agrupados por recurso
│   └── static/                Sitio público y panel administrativo (HTML/CSS/JS)
├── migrations/                Migraciones versionadas (Alembic)
├── fuentes/                    Directorio oficial de la CSJ Lima (PDF)
├── tests/                      Pruebas automatizadas (pytest)
├── prototipo-v1/                Micrositio estático, sin backend
├── DirectorioCSJLI.xlsx         Datos reales -- los usa app/cargar_directorio_excel.py y render.yaml
├── ConformacionCSJLima.xlsx     Datos reales -- los usa app/cargar_titulares.py y render.yaml
├── .env.example                  Plantilla de variables de entorno
├── alembic.ini
├── requirements.txt
├── run.py
├── backup_db.py
└── render.yaml
```

## 22. De dónde salen los datos reales

El catálogo se cargó desde el [Directorio Telefónico oficial de la CSJ Lima](https://www.pj.gob.pe)
(`fuentes/Directorio_CSJLI_oficial_2025-05-08.pdf`) -- 26 sedes y 584 dependencias al momento de
escribir esto, cifra que crece mientras cada área revisa y aprueba su parte. El cargador
(`python -m app.cargar_directorio_pj`) extrae las tablas con `pdfplumber` y no duplica registros si se
vuelve a ejecutar. Al cargar por primera vez, solo la sede piloto se publica como `activo`; el resto
queda en `revision` hasta que cada área la valide.

## 23. Integración continua (CI)

Cada `push` y Pull Request a `master` corre la suite completa de pruebas en GitHub Actions
(`.github/workflows/tests.yml`, contra SQLite en memoria, igual que en local) -- el resultado se ve en
la pestaña "Actions" del repositorio.

## 24. Solución de problemas

| Error | Causa / solución |
|---|---|
| `ModuleNotFoundError` | El entorno virtual no está activo, o falta `pip install -r requirements.txt`. |
| `connection refused` a PostgreSQL | Revisar servidor, puerto 5432, usuario, contraseña, firewall, `pg_hba.conf`, `postgresql.conf`. |
| `password authentication failed` | La contraseña en `DATABASE_URL` no coincide con la del usuario de PostgreSQL. |
| `database "justicia_orienta" does not exist` | Falta `CREATE DATABASE justicia_orienta OWNER justicia_app;`. |
| `alembic upgrade head` falla | `alembic current` / `alembic heads`, y confirmar que `DATABASE_URL` apunta a la base correcta. |
| Funciona en `localhost` pero no desde otra PC | Confirmar `--host 0.0.0.0`, el puerto, el firewall de Windows y la IP del servidor (`Test-NetConnection IP -Port 8743`). |
| El sitio abre pero no hay información | Cargar el catálogo (sección 9) y revisar el estado de los registros en `/admin`. |
| Los datos existen pero no aparecen en público | Revisar su estado editorial -- solo se publica lo `activo` (ver sección de Roles). |

## 25. Checklist final de instalación

```
[ ] Git, Python 3.10+ y PostgreSQL instalados
[ ] Usuario y base de datos de PostgreSQL creados
[ ] Repositorio clonado
[ ] Entorno virtual creado y activado
[ ] pip install -r requirements.txt
[ ] .env creado y configurado (DATABASE_URL, JUSTICIA_ORIENTA_SECRET, ENTORNO)
[ ] alembic upgrade head
[ ] app.seed
[ ] Catálogo cargado
[ ] pytest (158 pruebas) en verde
[ ] auditoria_accesibilidad revisada
[ ] python run.py levanta sin errores
[ ] / , /admin y /api/docs responden
[ ] Accesible desde otra PC de la LAN (si corresponde)
[ ] Firewall configurado (si corresponde)
[ ] Servicio de Windows configurado (si es servidor permanente)
[ ] Respaldo (backup_db.py) probado al menos una vez
[ ] Flujo gestor → validador → publicación probado de punta a punta
[ ] Si es de acceso público: HTTPS + dominio + infraestructura institucional
```
