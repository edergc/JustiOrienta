# Justicia Orienta

Orientador ciudadano accesible para la Corte Superior de Justicia de Lima: un sitio público donde
cualquier persona escribe o dicta en lenguaje natural qué trámite necesita ("dónde pago una multa",
"necesito el juzgado de familia") y el sistema responde con la dependencia exacta — sede, piso, horario,
requisitos y accesibilidad — sin inventar nada; si no tiene certeza, deriva a atención humana. Cada área
de la Corte mantiene su propia información desde un panel administrativo con control de roles, y todo
cambio pasa por un flujo de revisión antes de publicarse.

Nació como una buena práctica postulada al Concurso "Gestores de Atención al Ciudadano" (ODANC Lima,
2026); este repositorio contiene la aplicación real (backend + panel + sitio público), no los documentos
del concurso.

Toda la tecnología es de código abierto y sin costo de licencia: Python, FastAPI, SQLAlchemy, PostgreSQL,
HTML/CSS/JS nativos (sin frameworks de frontend).

## Qué ofrece

**Al ciudadano** (sitio público, `/`):

- Búsqueda por texto o por voz (reconocimiento de habla nativo del navegador, sin servicios de terceros),
  con interpretación de lenguaje natural (tolera errores de tipeo, frases de cortesía, sinónimos).
- Accesibilidad de verdad: alto contraste, texto ampliable, tema oscuro, lectura en voz alta de cada
  resultado — no como una fase futura, sino desde la primera versión.
- Ruta interna paso a paso dentro del edificio ("¿cómo llego desde aquí?"), con variante que evita
  escaleras, en las sedes donde ya se cargó el mapa interno.
- Solicitar que le llamen o le escriban cuando no encuentra lo que busca, con código de seguimiento.
- Directorio completo descargable en PDF, para imprimir o usar sin conexión.
- Acceso directo por código QR de sede o de dependencia (para carteles físicos).

**A cada área de la Corte** (panel administrativo, `/admin`):

- Gestión de su propio catálogo (dependencias, servicios, horarios, requisitos, accesibilidad), con
  flujo de revisión: nadie se autopublica, un(a) validador(a) aprueba antes de que algo llegue al
  ciudadano.
- Mapa interno (nodos y conexiones) para habilitar el cálculo de ruta.
- Indicadores: % de acierto de búsquedas, consultas sin resultado, pendientes de aprobar por área,
  completitud de datos, uso por sede/accesibilidad/voz — con reporte descargable en Excel.
- Auditoría completa (quién hizo qué, cuándo, desde qué IP), filtrable y exportable.
- Exportación del catálogo completo a Excel, código QR por sede/dependencia, gestión de usuarios y roles.

## Cómo replicar el sistema (levantar la aplicación)

Requiere **Python 3.10+** (ya viene con `pip`).

```bash
git clone <url-de-este-repositorio>
cd JustiOrienta
pip install -r requirements.txt

# 1. Configura el entorno
cp .env.example .env
# abre .env y ajusta DATABASE_URL / JUSTICIA_ORIENTA_SECRET (ver "Base de datos" y "Seguridad" abajo)

# 2. Crea el esquema de la base de datos (migraciones versionadas con Alembic)
python -m alembic upgrade head

# 3. Crea el usuario administrador inicial
python -m app.seed

# 4. Carga un catálogo para probar -- dos formas:
#    a) el directorio oficial real de la CSJ Lima, ya incluido en el repo:
python -m app.cargar_directorio_pj
#    b) o tu propio Excel, con las columnas que espera app/import_excel.py
#       (usa "Exportar catálogo" desde /admin una vez que tengas datos, para
#       obtener un archivo con el formato exacto y reimportarlo donde quieras):
python -m app.import_excel "tu_archivo.xlsx"

# 5. Levanta el servidor (backend y frontend son el mismo proceso, un solo puerto)
python run.py
```

Luego abre:

- **http://127.0.0.1:8743/** — el micrositio público (lo que ve el ciudadano).
- **http://127.0.0.1:8743/admin** — el panel de administración (lo que usa cada área para mantener su información).
  - Usuario inicial: DNI `12345678` / contraseña impresa por `app.seed` -- el panel **exige cambiarla**
    apenas inicias sesión, no es solo una sugerencia: `app.seed` y cualquier cuenta creada o restablecida
    desde `/admin` → Usuarios queda marcada para elegir una contraseña propia antes de poder usar el resto
    del sistema (el backend rechaza cualquier otro endpoint con 403 mientras eso no pase). El
    acceso es por DNI (8 dígitos), no por correo -- es el dato que toda persona en Perú tiene con
    certeza, a diferencia de una cuenta de correo institucional que no todas las áreas tienen asignada.
    Justamente porque el DNI es un dato público (no un secreto), el login se bloquea 15 minutos después de
    5 intentos fallidos seguidos con esa cuenta -- la contraseña es la única barrera real contra fuerza
    bruta y necesitaba esta protección. Guardar la ficha del usuario desde `/admin` → Usuarios → Editar
    levanta el bloqueo de inmediato, sin esperar los 15 minutos.
- **http://127.0.0.1:8743/api/docs** — documentación interactiva de la API (generada automáticamente por
  FastAPI). No está enlazada desde el sitio público -- es para quien desarrolla, no para el ciudadano.

### Ejecutar las pruebas automatizadas

```bash
python -m pytest
```

Son 158 pruebas (mismas que corren en GitHub Actions, ver más abajo), contra una base de datos SQLite en
memoria, aislada de tu base de desarrollo. Cubren, entre otras cosas:

- El buscador (lenguaje natural, tolerancia a errores de tipeo, regresiones ya encontradas) y el detector
  de duplicados.
- El flujo de publicación completo por rol y por área (quién puede crear, editar, aprobar y auditar), y
  que nadie pueda autopublicarse ni reasignar contenido a un área ajena.
- Autenticación: contraseña obligatoria en el primer ingreso, bloqueo tras 5 intentos fallidos,
  restablecer contraseña por correo, paginación y gestión de usuarios.
- El mapa interno / wayfinding (cálculo de ruta más corta, variante accesible sin escaleras).
- Solicitudes de atención ("que me llamen o me escriban") y solicitudes de cobertura.
- Sedes, edificios y servicios (incluida la reactivación de servicios desactivados).
- Indicadores editoriales, satisfacción de búsqueda, exportación del catálogo a Excel y el directorio en PDF.
- Una auditoría de accesibilidad estática sobre el HTML servido (`app/auditoria_accesibilidad.py`): idioma
  declarado, imágenes con texto alternativo, cada control de formulario con una etiqueta programática,
  botones/enlaces con nombre accesible, y diálogos modales con nombre accesible. Es una versión ligera de
  lo que haría axe-core, sin depender de Node ni de un navegador headless -- corre en cada `pytest` y
  también sola:

```bash
python -m app.auditoria_accesibilidad
```

No reemplaza una revisión real con lector de pantalla ni verifica contraste de color (eso necesita
render real), pero deja evidencia objetiva y repetible en cada cambio de plantilla.

### Sobre el puerto

`app/main.py` sirve el sitio público, el panel de administración y la API desde el
**mismo proceso** (así evita tener que correr y sincronizar dos servidores distintos
en el piloto). Por eso hay un solo puerto, no uno de "backend" y otro de "frontend".

Por defecto es **8743**, elegido a propósito para no chocar con puertos comunes de
otras herramientas que suelen correr en la misma máquina de desarrollo: ni
3000/3001/5173/5174/5180 (típicos de Vite/React), ni 8000/8001/4100/8085 (típicos de
otros backends). Si aun así choca en tu equipo, cámbialo sin tocar código:

```bash
PORT=9231 python run.py       # Windows PowerShell: $env:PORT=9231; python run.py
```

### Roles y flujo editorial

Cinco roles. Cada uno mapea directamente a la gobernanza descrita en la ficha de buena práctica:

| Rol | Puede |
|---|---|
| **admin** | Todo: sedes, edificios, usuarios, dependencias y servicios de cualquier área, aprobar cualquier cosa. |
| **gestor** | Crear/editar dependencias y servicios **solo de su propia área**. Nunca publica directamente: todo lo que guarda queda (o vuelve a) en estado `revision`. |
| **validador** | Lo mismo que gestor, más la capacidad de **aprobar** (`revision` → `activo`) o **devolver a revisión** contenido de su propia área. |
| **auditor** | Solo lectura de `/admin/auditoria` (el detalle de quién cambió qué) y de los indicadores. No puede crear ni editar nada. |
| **consulta** | Pensado para quien toma decisiones y supervisa, no para el día a día operativo: al entrar ve directo el panel de indicadores, el botón para descargar el reporte en Excel, y la pestaña "Auditoría" (quién cambió qué, y el detector de posibles duplicados) en solo lectura -- sin las pestañas de gestión del catálogo (crear/editar dependencias, sedes, usuarios), eso sigue siendo de cada área desde su propio rol. |

Ningún rol distinto de admin puede publicarse a sí mismo con solo guardar el formulario: aunque el
payload incluya `estado: "activo"`, el servidor lo regresa a `revision` si quien edita no tiene permiso
de aprobar esa área. Publicar es siempre una acción explícita (`POST /dependencias/{id}/aprobar`).

Por el mismo motivo, tampoco se puede "editarse a sí mismo" hacia otra área: solo admin puede cambiar el
campo `area` de una dependencia existente. Un(a) gestor(a) o validador(a) que edita algo de su propia
área no puede reescribir ese campo hacia un área distinta -- eso equivaldría a transferir contenido sin
que nadie del área destino lo autorizara.

Flujo típico: cada área carga o corrige su parte desde `/admin` → Dependencias (o vía Excel, ver arriba);
un(a) validador(a) de esa misma área revisa lo que está "En revisión" y lo aprueba o lo devuelve; el
micrositio público solo muestra lo `activo` -- nada llega al ciudadano sin ese segundo par de ojos; y todo
cambio queda en `/admin` → Auditoría.

Sedes y edificios son entidades propias (`/admin/sedes`, `/admin/edificios`) que cualquier dependencia
referencia -- no texto libre repetido en cada fila. Cada dependencia puede además tener uno o más
**servicios** estructurados (requisitos, canal, horario propios) además de su resumen general.

### Base de datos: PostgreSQL

Este proyecto corre sobre **PostgreSQL** — no SQLite. La app soporta ambos motores sin tocar código (vía
`DATABASE_URL`), pero el entorno real de este repositorio ya está configurado y probado sobre Postgres, con
el esquema completo, el directorio oficial real cargado (26 sedes, 584 dependencias vía
`python -m app.cargar_directorio_pj` -- la cifra crece a medida que cada área carga/aprueba más contenido,
así que tómala como referencia, no como un total fijo) y el flujo completo (crear → revisar → aprobar →
aparece en el sitio público, el PDF, el Excel exportado y la auditoría) verificado contra esa base:

```
DATABASE_URL=postgresql+psycopg2://usuario:clave@host:5432/justicia_orienta
```

```bash
pip install -r requirements.txt   # incluye psycopg2-binary
python -m alembic upgrade head
python -m app.seed                # crea el usuario administrador inicial
```

Copia `.env.example` a `.env` y ajusta los valores (incluida `JUSTICIA_ORIENTA_SECRET`, que firma las
sesiones — cámbiala antes de cualquier uso real). Ese `.env` nunca se sube al repositorio (está en
`.gitignore`) — cada máquina que corra el proyecto necesita el suyo con sus propias credenciales.

`app/config.py` conserva SQLite (`justicia_orienta.db`) como valor por defecto en el código *solo* como
resguardo de cero-instalación para quien clone el repo sin Postgres a mano (por ejemplo, para evaluarlo
rápido) -- nunca se usa mientras exista un `.env` con `DATABASE_URL` apuntando a Postgres, que es el caso de
este entorno.

Si cambias los modelos en `app/models/`, genera la migración correspondiente:

```bash
python -m alembic revision --autogenerate -m "descripción del cambio"
python -m alembic upgrade head
```

### Respaldos y registro de errores

```bash
python backup_db.py
```

Detecta solo el motor configurado en `DATABASE_URL` y hace lo correcto para cada uno, mismo comando en
los dos casos: copia el archivo `.db` a `backups/` en SQLite, o corre `pg_dump -Fc` (formato comprimido,
restaurable con `pg_restore`) en PostgreSQL. Es una acción manual y explícita (no corre sola ni
programada): antes de cargar datos nuevos, o como rutina periódica de quien administra el sistema. Cada
respaldo queda con marca de fecha y hora, y los de más de 30 días se purgan automáticamente para que
`backups/` no crezca sin límite -- ajusta `DIAS_RETENCION` en `backup_db.py` si tu política institucional
pide otra retención. Requiere que `pg_dump` esté instalado y en el `PATH` (viene con cualquier instalación
de PostgreSQL); si además necesitas una copia automatizada y programada (no solo manual), eso se agrega
con el Programador de tareas de Windows o `cron`, apuntando a este mismo comando.

Los errores del servidor quedan en `logs/justicia_orienta.log` (rotación automática: 1 MB por archivo,
5 respaldos), además de la consola -- así se puede revisar qué pasó después de un reinicio, sin depender
de una terminal que ya se cerró.

**Sobre HTTPS**: el piloto corre en HTTP simple porque `127.0.0.1`/red interna no lo necesita para
pruebas. Antes de exponer esto en un dominio público, es obligatorio ponerlo detrás de HTTPS (por
ejemplo con un proxy inverso como Caddy o Nginx + Let's Encrypt, o el balanceador que use la institución)
-- eso es una decisión de infraestructura de Informática, no algo que este repositorio pueda resolver
por sí solo corriendo en `127.0.0.1`.

## Seguridad

Pensado para que el equipo de TI que lo pruebe (incluida una prueba de intrusión) sepa exactamente qué
esperar, sin tener que leer el código para encontrarlo:

- **Secreto de sesión obligatorio en producción**: si `ENTORNO=produccion` y `JUSTICIA_ORIENTA_SECRET`
  sigue con el valor de relleno de `.env.example`, el servidor **se niega a arrancar**
  (`RuntimeError` en `app/main.py`) en vez de correr con una clave que cualquiera que lea el repositorio
  público podría usar para forjar un token válido, incluido uno de administrador. En desarrollo
  (`ENTORNO=desarrollo`, el valor por defecto si no se define) no aplica, para no exigir configuración
  extra solo para probar en local.
- **Contraseñas con bcrypt** (nunca en texto plano ni con hash reversible) y **bloqueo de cuenta**: 5
  intentos fallidos seguidos bloquean esa cuenta 15 minutos (ver la sección de roles más arriba);
  guardar la ficha del usuario desde `/admin` → Usuarios levanta el bloqueo antes si hace falta.
- **Limitador de tasa en memoria** (`app/rate_limit.py`, sin Redis ni servicios de pago) sobre los dos
  endpoints públicos sin autenticación que más se prestan a abuso: "olvidé mi contraseña" (máx. 3 por DNI
  y 10 por IP cada 15 min) y "que me llamen o me escriban" (máx. 5 solicitudes y 20 consultas de estado
  por IP cada 15 min).
- **Cabeceras de seguridad HTTP** en cada respuesta (middleware en `app/main.py`): `Content-Security-Policy`
  estricto (sin `unsafe-inline` para scripts, todo bajo `'self'`), `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY` (evita que el sitio se cargue dentro de un `<iframe>` de otro dominio,
  clickjacking), `Referrer-Policy`, `Permissions-Policy` (solo micrófono habilitado -- lo usa la
  búsqueda por voz -- cámara/geolocalización/pago bloqueados) y `Strict-Transport-Security` (HSTS -- el
  navegador solo la respeta sobre HTTPS real, así que no rompe nada corriendo en HTTP local).
- **Toda entrada de texto libre se escapa antes de mostrarse** en el panel administrativo y en el sitio
  público (`escaparHtml()` / `escaparHtmlPublico()` en `app/static/js/`), y toda celda exportada a Excel
  se neutraliza contra inyección de fórmulas (`app/excel_utils.py`: cualquier valor que empiece con
  `=`, `+`, `-` o `@` se antepone con `'` antes de escribirse).
- **Auditoría con contexto forense**: cada evento de sesión (`LOGIN_OK`, `LOGIN_FALLIDO`,
  `CUENTA_BLOQUEADA`, `CAMBIO_PASSWORD`, restablecimiento por token) y cada exportación (catálogo,
  reporte de indicadores, la propia auditoría) queda registrado con la IP de origen, no solo el cambio.
  `/admin` → Auditoría permite filtrar por DNI, entidad, acción y rango de fechas, y exportar el
  resultado filtrado a Excel (`GET /api/v1/admin/auditoria/exportar.xlsx`) -- para entregarlo directo a
  quien haga la prueba, sin que necesite acceso al sistema. Ningún rol, ni siquiera administrador, puede
  editar o borrar un registro de auditoría ya escrito.
- **Base de datos por defecto en el código es SQLite** (`app/config.py`) solo como resguardo de
  cero-instalación para quien clona el repo sin Postgres a mano -- nunca se usa mientras exista un `.env`
  con `DATABASE_URL` apuntando a Postgres, que es el caso de este entorno real.
- **Fuera del alcance de este repositorio** (decisión de infraestructura, no de código): en producción,
  el rol de base de datos que usa la app debería tener permiso de `INSERT`/`SELECT` sobre la tabla
  `auditoria` pero no `UPDATE`/`DELETE`, para que ni un bug ni una cuenta admin comprometida puedan
  alterar el rastro ya escrito.

## De dónde salen los datos reales

El catálogo ya **no** tiene datos de ejemplo: se cargó el
[Directorio Telefónico oficial de la CSJ Lima](https://www.pj.gob.pe), publicado por el propio Poder
Judicial (`fuentes/Directorio_CSJLI_oficial_2025-05-08.pdf`, actualizado al 26 de junio de 2026) —
**26 sedes y 584 dependencias** al momento de escribir esto, con dirección, piso y anexo reales (la
cifra sigue creciendo mientras cada área revisa y aprueba su parte).

```bash
python -m app.cargar_directorio_pj
```

Extrae las tablas del PDF con `pdfplumber` (no transcripción a mano, para no meter errores de tipeo en
cientos de filas) y las inserta sin duplicar si se vuelve a correr. Reglas que sigue, alineadas con
"nunca inventar información":

- Solo carga lo que el documento realmente dice: sede, dirección, central, dependencia, piso, anexo.
  Horario, requisitos, accesibilidad y alias quedan en blanco — son trabajo de revisión de cada área,
  no algo que un script deba adivinar.
- Al cargar el directorio por primera vez, solo la **sede piloto** (Javier Alzamora Valdez) se publica
  como `activo`; el resto queda en `revision`, lista para que cada una la revise antes de publicarla —
  cargar en masa no es lo mismo que validar. (En este entorno ya se revisaron y aprobaron todas.)
- Si el mismo PDF (u otra versión más nueva del Poder Judicial) se vuelve a procesar, no duplica lo que
  ya existe.

**Limitación real, ya encontrada:** el documento fuente repite nombres genéricos como "Mesa de Partes"
para oficinas distintas dentro de la misma sede (Bienestar Social, Control de Asistencia, Escalafón y
Registro) — quedaban 3 tarjetas idénticas en el buscador. Se corrigieron a mano restaurando el contexto
que sí figura en el PDF (ver `/admin` → Auditoría), y el cargador ya sabe no volver a duplicarlas.

## Arquitectura del backend

Organizado por responsabilidad, no en un archivo gigante — cada capa tiene su propio paquete:

```
app/
  config.py          Configuración centralizada (pydantic-settings, lee .env)
  database.py        Motor SQLAlchemy y sesión
  security.py        Hash de contraseñas, JWT, reglas de permiso por rol/área
  nlp.py              Interpretación de lenguaje natural del buscador
  main.py            Arma la app, monta routers, maneja errores, cabeceras de seguridad

  models/            Una tabla por archivo (Sede, Edificio, Dependencia, Servicio,
                      Alias, Usuario, Auditoria, ConsultaLog, SolicitudAtencion,
                      SolicitudCobertura, NodoUbicacion, ConexionNodo)
  schemas/           Esquemas Pydantic de entrada/salida, uno por entidad
  crud/              Acceso a datos y reglas de negocio, uno por entidad
  routers/           Endpoints HTTP, agrupados por recurso: auth, public,
                      admin_dependencias, admin_sedes, admin_edificios, admin_mapa,
                      admin_usuarios, admin_auditoria, admin_metricas,
                      admin_cobertura, admin_solicitudes_atencion, admin_qr
                      (no un solo admin.py)
  rutas_internas.py  Cálculo de ruta más corta (Dijkstra) sobre el grafo de
                      nodos/conexiones del mapa interno -- usado por admin_mapa.py
                      y por el endpoint público /ruta
  rate_limit.py      Limitador de tasa simple en memoria (sin Redis ni
                      servicios de pago) para "olvidé mi contraseña" y
                      "que me llamen o me escriban"
  static/            El sitio público y el panel de administración (HTML/CSS/JS)
```

La API vive bajo `/api/v1` (versionada desde el día uno: si en el futuro cambia algo de forma
incompatible, puede convivir `/api/v2` sin romper lo existente).

### Integración continua

Cada `push` y cada Pull Request a `master` corre la suite de pruebas automáticamente en GitHub Actions
(`.github/workflows/tests.yml`, contra SQLite en memoria, igual que en local) -- así cualquier cambio que
rompa algo se detecta antes de fusionarse, sin depender de que quien revisa se acuerde de correr
`pytest` a mano. El resultado se ve en la pestaña "Actions" del repositorio en GitHub.

## Qué hay en este repositorio

| Archivo / carpeta | Qué es |
|---|---|
| `app/` | La aplicación: backend FastAPI + base de datos + sitio público + panel de administración. |
| `prototipo-v1/` | Micrositio estático de un solo archivo, sin backend -- demuestra el concepto sin instalar nada. |
| `migrations/` | Migraciones versionadas de la base de datos (Alembic). |
| `fuentes/` | Directorio oficial de la CSJ Lima usado como fuente de datos reales (ver "De dónde salen los datos reales"). |
| `tests/` | Pruebas automatizadas (`pytest`). |
| `.github/workflows/` | Integración continua (corre `pytest` en cada push/PR). |
| `run.py` | Punto de arranque único del servidor. |
| `backup_db.py` | Respaldo manual de la base de datos (SQLite o PostgreSQL). |
| `requirements.txt` | Dependencias Python. |
| `alembic.ini` | Configuración de migraciones. |
| `.env.example` | Plantilla de variables de entorno -- cópiala a `.env` y ajusta los valores. |

## Hoja de ruta (de dónde venimos, hacia dónde va)

| Fase | Qué es | Estado |
|---|---|---|
| V0 | Protocolo humano + catálogo en papel/Excel | Diseñado (ficha de buena práctica) |
| V1 | Micrositio estático, sin backend | Hecho — `prototipo-v1/` |
| **V2** | **Backend real + base de datos + panel de administración con roles** | **Hecho — `app/`, esto es lo que estás viendo** |
| V3 | Interpretación de lenguaje natural sobre el catálogo validado | Hecho — `app/nlp.py` (reglas explícitas y auditables, no un modelo de IA -- decisión deliberada, ver "Principios que no se negocian" más abajo) |
| V4 | Navegación interior (mapa interno + cálculo de ruta más corta) | Hecho — `app/rutas_internas.py`, pestaña "Mapa interno" en `/admin`. Otras integraciones (ej. con sistemas externos de la institución): no iniciado |

## Principios que no se negocian

- **Nunca inventar información institucional.** Si el buscador no tiene certeza, deriva a atención humana
  en vez de adivinar (ver el mensaje de respaldo en `/api/v1/buscar`).
- **Cada área es dueña de su información.** Gestores y validadores solo tocan las dependencias de su
  propia área; Informática administra la plataforma, no decide el contenido de otras áreas.
- **Nadie se autopublica.** Todo cambio de contenido pasa a revisión; publicar es una acción explícita de
  quien tiene el rol de validador o administrador.
- **Accesibilidad no es una fase futura.** Alto contraste, texto ampliable y lectura en voz alta están en
  el V1 y el V2, no reservados para una versión posterior.
