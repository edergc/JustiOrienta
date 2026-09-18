# Justicia Orienta — Guía de despliegue

Orientador ciudadano accesible para la Corte Superior de Justicia de Lima: sitio público de búsqueda en
lenguaje natural + panel administrativo por roles, servidos por un único backend FastAPI + PostgreSQL.

**Repositorio:** https://github.com/edergc/JustiOrienta

---

## Instalación rápida

Con esto la aplicación queda funcionando en tu máquina o en un servidor. Todo lo demás (LAN, servicio de
Windows, respaldos, seguridad, Render, solución de problemas) está en la sección **Referencia**, más
abajo -- no hace falta leerlo para el primer despliegue.

Requisitos: Git, Python 3.10+, PostgreSQL (cliente `psql`/`pg_dump`/`pg_restore` incluido). Nada de
Node.js, Docker ni servicios externos -- todo lo demás lo instala `pip`.

```bash
# 1. Clonar
git clone https://github.com/edergc/JustiOrienta.git
cd JustiOrienta

# 2. Entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1              # Linux/macOS: source .venv/bin/activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
cp .env.example .env                       # Windows: Copy-Item .env.example .env
# Editar .env: como mínimo, DATABASE_URL y JUSTICIA_ORIENTA_SECRET (ver "Variables de .env" abajo)

# 5. Crear la base de datos en PostgreSQL (para SQLite, saltar este paso)
psql -U postgres -c "CREATE USER justicia_app WITH PASSWORD 'clave';"
psql -U postgres -c "CREATE DATABASE justicia_orienta OWNER justicia_app;"

# 6. Crear las tablas
python -m alembic upgrade head

# 7. Crear el usuario administrador
python -m app.seed

# 8. Cargar el catálogo (directorio oficial de la CSJ Lima, ya incluido en el repo)
python -m app.cargar_directorio_pj

# 9. Levantar el servidor
python run.py
```

## Probar que funcionó

- http://127.0.0.1:8743/ → sitio público (escribe algo como "juzgado de familia" en el buscador)
- http://127.0.0.1:8743/admin → panel administrativo (DNI `12345678` + la contraseña que imprimió `app.seed` -- pide cambiarla al entrar)
- http://127.0.0.1:8743/api/docs → documentación de la API

```bash
python -m pytest    # 158 pruebas automatizadas -- deben pasar todas
```

Si los tres enlaces abren, el buscador devuelve resultados y `pytest` pasa en verde: el despliegue
funcionó. Todo lo que sigue es referencia para profundizar, no pasos adicionales obligatorios.

---

## Referencia

### Usar SQLite en vez de PostgreSQL (para evaluar rápido, sin instalar nada)

Dejar `.env` con el valor por defecto (`DATABASE_URL=sqlite:///./justicia_orienta.db`) y saltar el paso 5
de arriba. Sirve para probar el sistema en minutos; para un servidor real, usar PostgreSQL.

### Variables de `.env`

`.env.example` trae todas las variables reales que lee `app/config.py`:

| Variable | Para qué |
|---|---|
| `ENTORNO` | `desarrollo` o `produccion`. En producción, si `JUSTICIA_ORIENTA_SECRET` sigue con el valor de relleno, el servidor **se niega a arrancar** (protección contra dejar la clave de ejemplo puesta). |
| `DATABASE_URL` | `postgresql+psycopg2://usuario:clave@host:5432/justicia_orienta` (o `sqlite:///./justicia_orienta.db`). |
| `JUSTICIA_ORIENTA_SECRET` | Firma las sesiones -- una clave larga y distinta en cada entorno. |
| `URL_PUBLICA` | Para armar el enlace del correo de "olvidé mi contraseña". |
| `SMTP_*` | Correo saliente para ese mismo flujo -- si se dejan vacías, el correo no se envía de verdad, solo queda en el log (para poder probar sin credenciales reales). |

`.env` nunca se sube al repositorio (está en `.gitignore`) -- cada máquina necesita el suyo.

### Si PostgreSQL está en otro servidor

```env
DATABASE_URL=postgresql+psycopg2://justicia_app:CLAVE@172.20.1.52:5432/justicia_orienta
```

El administrador de PostgreSQL debe permitir la conexión desde el servidor de la aplicación
(`pg_hba.conf`), escuchar en la interfaz correcta (`postgresql.conf`), y debe haber conectividad TCP al
puerto 5432 entre ambos servidores.

### Acceso desde otra PC de la LAN

Por defecto el servidor escucha solo en `127.0.0.1`. `run.py` ya lo expone en todas las interfaces vía
`HOST=0.0.0.0` -- solo falta abrir el puerto en el firewall de Windows si corresponde:

```powershell
New-NetFirewallRule -DisplayName "Justicia Orienta - TCP 8743" -Direction Inbound -Protocol TCP -LocalPort 8743 -Action Allow
```

Luego, desde otro equipo: `http://IP_DEL_SERVIDOR:8743/` (ver la IP con `ipconfig`).

### Crear un servicio de Windows (para que no dependa de una consola abierta)

Primero comprobar manualmente que todo funciona (los pasos de "Instalación rápida"). Recién entonces
convertirlo en servicio, por ejemplo con **NSSM**:

| Parámetro | Valor |
|---|---|
| Programa | `C:\JusticiaOrienta\.venv\Scripts\python.exe` |
| Argumentos | `-m uvicorn app.main:app --host 0.0.0.0 --port 8743` |
| Directorio | `C:\JusticiaOrienta` |
| Variables de entorno | Las mismas de `.env` (`DATABASE_URL`, `ENTORNO=produccion`, `JUSTICIA_ORIENTA_SECRET`) |

### Roles (para probar el flujo editorial completo, no solo que la app prenda)

| Rol | Puede |
|---|---|
| **admin** | Todo: sedes, edificios, usuarios, dependencias y servicios de cualquier área; aprobar cualquier cosa. |
| **gestor** | Crear/editar solo de su propia área. Nunca publica directamente: queda en `revision`. |
| **validador** | Lo mismo que gestor, más aprobar o devolver a revisión contenido de su propia área. |
| **auditor** | Solo lectura de auditoría e indicadores. |
| **consulta** | Indicadores, reporte en Excel y auditoría en solo lectura. |

Prueba mínima del flujo: un(a) gestor(a) crea una dependencia (queda en `revision`) → un(a) validador(a)
la aprueba → recién ahí aparece en el sitio público. Todo queda registrado en `/admin` → Auditoría, con
la IP de origen.

### Cargar el catálogo -- otras opciones

Además de `python -m app.cargar_directorio_pj` (opción usada en "Instalación rápida"):

```bash
python -m app.import_excel "tu_archivo.xlsx"      # Excel propio (columnas: ver app/import_excel.py)
```

El repositorio también incluye `DirectorioCSJLI.xlsx` y `ConformacionCSJLima.xlsx`, datos reales que
usan `app/cargar_directorio_excel.py` y `app/cargar_titulares.py` respectivamente -- son los que corre
`render.yaml` en cada despliegue (ver "Despliegue alternativo: Render" abajo). No son duplicados del PDF
de `fuentes/`: alimentan un flujo de carga distinto, no los borres ni los muevas del repositorio.

### Migraciones futuras

Si se modifica un modelo en `app/models/`, no se toca la estructura de producción a mano:

```bash
python -m alembic revision --autogenerate -m "descripción del cambio"
# revisar el archivo generado en migrations/versions/, luego:
python -m alembic upgrade head
```

### Respaldos y restauración

```bash
python backup_db.py
```

Detecta el motor por `DATABASE_URL` (mismo comando para los dos). En PostgreSQL corre `pg_dump -Fc`
hacia `backups/`, con fecha y hora; los de más de 30 días se purgan solos. Es manual y explícito -- para
automatizarlo, agendar este mismo comando con el Programador de tareas de Windows o `cron`.

**Restaurar** (PostgreSQL):

```bash
createdb -U postgres justicia_orienta          # solo si la base todavía no existe
pg_restore -h localhost -U justicia_app -d justicia_orienta backups/justicia_orienta_FECHA.dump
python -m alembic upgrade head                 # solo si el código tiene migraciones más nuevas que el respaldo
```

El `.dump` ya trae esquema y datos juntos -- no hace falta `app.seed` ni recargar el catálogo. En
SQLite, restaurar es copiar el archivo `.db` de vuelta. Tratar esto como una operación controlada:
confirmar primero que el destino es realmente la base que se quiere sobrescribir.

### Logs y diagnóstico

Errores del servidor en `logs/justicia_orienta.log` (rotación automática), además de la consola.

| Síntoma | Qué revisar |
|---|---|
| `ModuleNotFoundError` | Entorno virtual no activo, o falta `pip install -r requirements.txt`. |
| `connection refused` a PostgreSQL | Servidor, puerto 5432, usuario/clave, firewall, `pg_hba.conf`. |
| `database "justicia_orienta" does not exist` | Falta el `CREATE DATABASE` del paso 5. |
| `alembic upgrade head` falla | `alembic current` / `alembic heads`; confirmar que `DATABASE_URL` apunta a la base correcta. |
| Funciona en `localhost` pero no desde otra PC | `--host 0.0.0.0`, firewall de Windows, IP correcta (`Test-NetConnection IP -Port 8743`). |
| El sitio abre pero no hay información | Repetir el paso 8 (cargar catálogo) y revisar `/admin`. |
| Hay datos pero no aparecen en público | Revisar su estado editorial -- solo se publica lo `activo` (ver "Roles"). |

### Despliegue alternativo: Render

El repositorio incluye `render.yaml` como referencia de despliegue en la nube (migraciones, admin,
carga de datos y arranque en un solo `startCommand`) -- no es la única forma de desplegar, documenta qué
pasos hacen falta en cualquier plataforma. Si se usa, hay que crear el Web Service apuntando a este
repositorio y configurar como variables de entorno (no en el repo): `DATABASE_URL`,
`JUSTICIA_ORIENTA_SECRET`, `URL_PUBLICA` y, opcionalmente, `SMTP_*`.

### Seguridad

- Secreto de sesión obligatorio en producción (ver "Variables de `.env`"); contraseñas con bcrypt;
  bloqueo de cuenta tras 5 intentos fallidos (15 min).
- Limitador de tasa en memoria (`app/rate_limit.py`) en "olvidé mi contraseña" y "que me llamen o me
  escriban".
- Cabeceras HTTP de seguridad en cada respuesta: CSP estricto, `X-Frame-Options: DENY`,
  `Referrer-Policy`, `Permissions-Policy`, HSTS.
- Escape de HTML en todo texto libre, y neutralización de fórmulas en cada celda exportada a Excel.
- Auditoría con IP de origen en cada login y exportación, filtrable desde `/admin` → Auditoría; ningún
  rol puede editar ni borrar un registro ya escrito.
- HTTPS obligatorio antes de exponer el sistema en un dominio público (proxy inverso con TLS) -- el
  piloto en LAN/`127.0.0.1` corre en HTTP simple.

### Estructura del repositorio

```
app/            Backend: config, database, security, nlp, routers/, crud/, models/, schemas/, static/
migrations/     Migraciones versionadas (Alembic)
fuentes/        Directorio oficial de la CSJ Lima (PDF)
tests/          Pruebas automatizadas (pytest)
prototipo-v1/   Micrositio estático, sin backend
.env.example    Plantilla de variables de entorno
run.py          Arranque del servidor
backup_db.py    Respaldo de la base de datos
render.yaml     Configuración de despliegue en Render (opcional)
```

### De dónde salen los datos reales

El catálogo se cargó desde el Directorio Telefónico oficial de la CSJ Lima
(`fuentes/Directorio_CSJLI_oficial_2025-05-08.pdf`) -- 26 sedes y 584 dependencias al momento de
escribir esto, cifra que crece mientras cada área revisa y aprueba su parte.

### Integración continua

Cada `push` y Pull Request a `master` corre las 158 pruebas en GitHub Actions
(`.github/workflows/tests.yml`, contra SQLite en memoria) -- resultado visible en la pestaña "Actions".

### Checklist detallado (para un despliegue institucional, no solo la prueba local)

```
[ ] Accesible desde otra PC de la LAN
[ ] Firewall configurado
[ ] Servicio de Windows configurado (si es servidor permanente)
[ ] Respaldo (backup_db.py) probado al menos una vez, y su restauración también
[ ] Flujo gestor → validador → publicación probado de punta a punta
[ ] Auditoría muestra las acciones anteriores con IP de origen
[ ] Si es de acceso público: HTTPS + dominio + infraestructura institucional
```
