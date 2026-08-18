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
| `JusticiaOrienta_05_Nota_Interna_para_Firma.docx` | Nota de una página, no anónima, para conseguir la autorización y firma del responsable. |
| `JusticiaOrienta_06_Manual_Panel_Administracion.docx` | Manual paso a paso, con capturas reales, para personal de área que no programa. |
| `JusticiaOrienta_07_Manual_Ciudadano.docx` | Guía en lenguaje simple para quien usa el sitio público, con capturas reales. |
| `prototipo-v1/` | **V1** — micrositio estático de un solo archivo, sin backend, para demostrar el concepto sin instalar nada. |
| `app/` | **V2** — aplicación real: backend FastAPI + base de datos + panel de administración. Esto es lo que sigue creciendo. |
| `migrations/` | Migraciones versionadas de la base de datos (Alembic). |
| `fuentes/` | Documentos oficiales usados como fuente de datos reales (ver más abajo). |
| `tests/` | Pruebas automatizadas (`pytest`). |
| `run.py` | Punto de arranque único del servidor. |
| `backup_db.py` | Respaldo manual de la base de datos (ver "Respaldos y registro de errores"). |

## Cómo correr la aplicación real (`app/`)

Requiere Python 3.10+ (ya viene con `pip`, no hace falta nada más para empezar).

```bash
pip install -r requirements.txt

# 1. Crea el esquema de la base de datos (migraciones versionadas con Alembic)
python -m alembic upgrade head

# 2. Crea el usuario administrador inicial
python -m app.seed

# 3. Carga el catálogo desde el Excel de levantamiento (real o de ejemplo)
python -m app.import_excel "JusticiaOrienta_04_Plantilla_Catalogo_Piloto.xlsx"

# 4. Levanta el servidor (backend y frontend son el mismo proceso, un solo puerto)
python run.py
```

Luego abre:

- **http://127.0.0.1:8743/** — el micrositio público (lo que ve el ciudadano).
- **http://127.0.0.1:8743/admin** — el panel de administración (lo que usa cada área para mantener su información).
  - Usuario inicial: DNI `12345678` / contraseña impresa por `app.seed` — **cámbiala de inmediato**. El
    acceso es por DNI (8 dígitos), no por correo -- es el dato que toda persona en Perú tiene con
    certeza, a diferencia de una cuenta de correo institucional que no todas las áreas tienen asignada.
- **http://127.0.0.1:8743/api/docs** — documentación interactiva de la API (generada automáticamente por
  FastAPI). No está enlazada desde el sitio público -- es para quien desarrolla, no para el ciudadano.

### Ejecutar las pruebas automatizadas

```bash
python -m pytest
```

Corren contra una base de datos SQLite en memoria, aislada de tu base de desarrollo. Cubren el
buscador (lenguaje natural, tolerancia a errores de tipeo, regresiones ya encontradas) y el flujo de
publicación completo (quién puede crear, editar, aprobar y auditar).

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

Si más adelante se separa el frontend en un proyecto propio (por ejemplo al construir
V3), lo natural será darle igualmente un puerto propio poco común y habilitar CORS en
la API para ese origen -- hoy no aplica porque ambos viven en el mismo proceso.

### Roles y flujo editorial

Cinco roles. Cada uno mapea directamente a la gobernanza descrita en la ficha de buena práctica:

| Rol | Puede |
|---|---|
| **admin** | Todo: sedes, edificios, usuarios, dependencias y servicios de cualquier área, aprobar cualquier cosa. |
| **gestor** | Crear/editar dependencias y servicios **solo de su propia área**. Nunca publica directamente: todo lo que guarda queda (o vuelve a) en estado `revision`. |
| **validador** | Lo mismo que gestor, más la capacidad de **aprobar** (`revision` → `activo`) o **devolver a revisión** contenido de su propia área. |
| **auditor** | Solo lectura de `/admin/auditoria` (el detalle de quién cambió qué) y de los indicadores. No puede crear ni editar nada. |
| **consulta** | Pensado para quien toma decisiones a partir de las estadísticas, no del día a día operativo: al entrar ve directo el panel de indicadores y el botón para descargar el reporte en Excel -- sin las pestañas de gestión del catálogo, y sin acceso al detalle de auditoría (eso sigue siendo solo admin/auditor). |

Ningún rol distinto de admin puede publicarse a sí mismo con solo guardar el formulario: aunque el
payload incluya `estado: "activo"`, el servidor lo regresa a `revision` si quien edita no tiene permiso
de aprobar esa área. Publicar es siempre una acción explícita (`POST /dependencias/{id}/aprobar`).

### Flujo de trabajo pensado para las áreas

1. Cada área llena o corrige su parte del Excel de levantamiento (`JusticiaOrienta_04...xlsx`), **o**
   un(a) gestor(a) de esa área carga la información directamente desde `/admin` → pestaña Dependencias.
2. Informática corre `python -m app.import_excel` para volcar el Excel a la base de datos cuando corresponda.
3. Un(a) validador(a) de esa misma área revisa lo que está "En revisión" y lo aprueba, o lo devuelve con
   un comentario.
4. El micrositio público (`/`) solo muestra dependencias en estado `activo` — nada llega al ciudadano sin
   pasar por ese segundo par de ojos.
5. Todo cambio (crear, editar, aprobar, rechazar, desactivar) queda en `/admin` → pestaña Auditoría:
   quién, cuándo, qué entidad, qué cambió.

Sedes y edificios ya no son texto libre repetido en cada fila: son entidades propias
(`/admin/sedes`, `/admin/edificios`) que cualquier dependencia referencia. Cada dependencia puede además
tener uno o más **servicios** estructurados (requisitos, canal, horario propios) además de su resumen
general.

### Producción vs. desarrollo

Por defecto la app usa SQLite (`justicia_orienta.db`, cero instalación). Para producción, define la
variable de entorno `DATABASE_URL` apuntando a PostgreSQL y corre las migraciones — no hay que tocar
código:

```
DATABASE_URL=postgresql+psycopg2://usuario:clave@host:5432/justicia_orienta
```

```bash
python -m alembic upgrade head
```

Copia `.env.example` a `.env` y ajusta los valores (incluida `JUSTICIA_ORIENTA_SECRET`, que firma las
sesiones — cámbiala antes de cualquier uso real).

Si cambias los modelos en `app/models/`, genera la migración correspondiente:

```bash
python -m alembic revision --autogenerate -m "descripción del cambio"
python -m alembic upgrade head
```

### Respaldos y registro de errores

```bash
python backup_db.py
```

Copia `justicia_orienta.db` a `backups/` con marca de fecha y hora. Es una acción manual y explícita
(no corre sola ni programada): antes de cargar datos nuevos, o como rutina periódica de quien administra
el sistema. En producción con PostgreSQL, este script se reemplaza por `pg_dump` según la política de
respaldos del área de TI -- no hay una versión propia para Postgres porque esa decisión (frecuencia,
retención, dónde se guarda) le corresponde a Informática, no a este repositorio.

Los errores del servidor quedan en `logs/justicia_orienta.log` (rotación automática: 1 MB por archivo,
5 respaldos), además de la consola -- así se puede revisar qué pasó después de un reinicio, sin depender
de una terminal que ya se cerró.

**Sobre HTTPS**: el piloto corre en HTTP simple porque `127.0.0.1`/red interna no lo necesita para
pruebas. Antes de exponer esto en un dominio público, es obligatorio ponerlo detrás de HTTPS (por
ejemplo con un proxy inverso como Caddy o Nginx + Let's Encrypt, o el balanceador que use la institución)
-- eso es una decisión de infraestructura de Informática, no algo que este repositorio pueda resolver
por sí solo corriendo en `127.0.0.1`.

## De dónde salen los datos reales

El catálogo ya **no** tiene datos de ejemplo: se cargó el
[Directorio Telefónico oficial de la CSJ Lima](https://www.pj.gob.pe), publicado por el propio Poder
Judicial (`fuentes/Directorio_CSJLI_oficial_2025-05-08.pdf`, actualizado al 26 de junio de 2026) —
**25 sedes y 542 dependencias**, con dirección, piso y anexo reales.

```bash
python -m app.cargar_directorio_pj
```

Extrae las tablas del PDF con `pdfplumber` (no transcripción a mano, para no meter errores de tipeo en
cientos de filas) y las inserta sin duplicar si se vuelve a correr. Reglas que sigue, alineadas con
"nunca inventar información":

- Solo carga lo que el documento realmente dice: sede, dirección, central, dependencia, piso, anexo.
  Horario, requisitos, accesibilidad y alias quedan en blanco — son trabajo de revisión de cada área,
  no algo que un script deba adivinar.
- Solo la **sede piloto** (Javier Alzamora Valdez) se publica como `activo`. Las otras 24 sedes quedan
  cargadas en `revision`, listas para que cada una las revise antes de publicarlas — cargar en masa no
  es lo mismo que validar.
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
  config.py         Configuración centralizada (pydantic-settings, lee .env)
  database.py       Motor SQLAlchemy y sesión
  security.py       Hash de contraseñas, JWT, reglas de permiso por rol/área
  nlp.py            Interpretación de lenguaje natural del buscador
  main.py           Arma la app, monta routers, maneja errores

  models/           Una tabla por archivo (Sede, Edificio, Dependencia, Servicio,
                     Alias, Usuario, Auditoria, ConsultaLog)
  schemas/          Esquemas Pydantic de entrada/salida, uno por entidad
  crud/             Acceso a datos y reglas de negocio, uno por entidad
  routers/          Endpoints HTTP, agrupados por recurso (no un solo admin.py)
  static/           El sitio público y el panel de administración (HTML/CSS/JS)
```

La API vive bajo `/api/v1` (versionada desde el día uno: si en el futuro cambia algo de forma
incompatible, puede convivir `/api/v2` sin romper lo existente).

## Hoja de ruta (de dónde venimos, hacia dónde va)

| Fase | Qué es | Estado |
|---|---|---|
| V0 | Protocolo humano + catálogo en papel/Excel | Diseñado (ficha de buena práctica) |
| V1 | Micrositio estático, sin backend | Hecho — `prototipo-v1/` |
| **V2** | **Backend real + base de datos + panel de administración con roles** | **Hecho — `app/`, esto es lo que estás viendo** |
| V3 | Asistente de interpretación de lenguaje natural sobre el catálogo validado | No iniciado |
| V4 | Navegación interior avanzada, integraciones adicionales | No iniciado |

## El panel de administración (`/admin`)

- **Cambiar mi contraseña**: cualquier usuario, sin importar el rol, puede cambiarla desde el botón junto a
  "Salir" -- pide la contraseña actual antes de aceptar la nueva.
- **Gestión completa de usuarios** (solo admin): editar nombre, rol, área, activar/desactivar y restablecer
  la contraseña de cualquier persona, sin tocar la base de datos a mano. Un(a) admin no puede desactivar su
  propia cuenta por accidente.
- **Sedes con estado real**: el formulario de sedes tiene un selector Activo/Inactivo -- antes se forzaba
  siempre a "activo" al guardar, así que editar una sede inactiva la reactivaba sin querer.
- **Paginación y búsqueda por nombre** en la tabla de dependencias, para catálogos grandes (10 por página,
  con "Mostrando X–Y de Z").
- **Código QR por sede y por dependencia** (botón "QR" en cada fila de la tabla de Sedes y de Dependencias):
  genera al vuelo, con la librería `qrcode` (100% local, sin servicio de terceros), un PNG que apunta al
  sitio público con el contexto ya resuelto (`?sede=<id>` o `?dependencia=<id>`) para imprimir y pegar en
  un cartel físico.
- **"Cómo llegar dentro del edificio"** (opcional, por dependencia): un campo de texto libre para
  indicaciones simples ("desde el ingreso principal, sube al piso 5 por el ascensor"). Es deliberadamente
  solo texto -- no un mapa interior ni geolocalización indoor, algo que este sistema no promete.
- **Panel de indicadores ampliado**: además de consultas totales/resueltas/satisfacción, muestra
  % de búsquedas hechas en modo accesible (alto contraste, texto ampliado o tema oscuro), % por voz,
  % sobre accesibilidad, consultas más frecuentes y consultas por sede/área/tipo -- los tres desgloses
  que pide la sección 30 del proyecto original.
- **Reporte descargable en Excel** (`GET /api/v1/admin/metricas/reporte.xlsx`, botón "Descargar reporte"
  visible para admin/auditor/consulta): la misma foto de indicadores del panel, en un `.xlsx` con una
  hoja de resumen y una hoja por cada desglose -- para llevar a una reunión sin depender de que quien lo
  necesita tenga acceso al sistema en ese momento. Generado con `openpyxl`, sin ningún servicio externo.
- Confirmaciones visuales (un aviso breve arriba a la derecha) después de cada guardado exitoso.

## El sitio público (`/`)

- **Búsqueda por texto o por voz**: el botón de micrófono usa reconocimiento de habla nativo del
  navegador (Web Speech API) — sin servicios de terceros. Si el navegador no lo soporta, o se niega el
  permiso, el buscador de texto sigue funcionando igual.
- **Estado vacío con sugerencias por categoría**: antes de escribir nada, la persona ve tres caminos
  claros ("encontrar un juzgado", "trámites administrativos", "no sé qué necesito") en vez de una
  pantalla en blanco.
- **Saludo contextual por QR de sede o de dependencia**: un enlace con `?sede=<id>` o `?dependencia=<id>`
  (los que llevaría el QR físico instalado en una sede o en la puerta de una oficina) muestra un aviso de
  contexto y, en el caso de `?dependencia=`, la ficha de esa oficina directamente, sin tener que buscarla.
- **Preguntas de accesibilidad respondidas directo**: si alguien escribe o dice algo como "¿hay rampa?" o
  "ascensor" y el sitio ya sabe en qué sede está (por el QR), responde de inmediato con la accesibilidad
  real de esa sede -- sin inventar nada: si no hay dato confirmado, lo dice así y deriva a atención humana.
- **Retroalimentación de una pregunta**: después de cada búsqueda, "¿Esto te resultó útil? Sí /
  Parcialmente / No" — anónimo, ligado solo al identificador de esa consulta puntual, visible en
  `/admin` → estadísticas (`porcentaje_satisfaccion`).
- Todo lo demás del diseño original se mantiene: alto contraste, texto ampliable, tema oscuro, lectura
  en voz alta de cada resultado, y el mensaje de respaldo cuando el sistema no tiene certeza.

## Principios que no se negocian

- **Nunca inventar información institucional.** Si el buscador no tiene certeza, deriva a atención humana
  en vez de adivinar (ver el mensaje de respaldo en `/api/v1/buscar`).
- **Cada área es dueña de su información.** Gestores y validadores solo tocan las dependencias de su
  propia área; Informática administra la plataforma, no decide el contenido de otras áreas.
- **Nadie se autopublica.** Todo cambio de contenido pasa a revisión; publicar es una acción explícita de
  quien tiene el rol de validador o administrador.
- **Accesibilidad no es una fase futura.** Alto contraste, texto ampliable y lectura en voz alta están en
  el V1 y el V2, no reservados para una versión posterior.
