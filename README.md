# ⚖️ Justicia Orienta

> **Orientador ciudadano accesible para la Corte Superior de Justicia de Lima**
>
> Aplicación web para orientar a la ciudadanía sobre **dónde, cómo y con quién realizar una gestión**, utilizando información institucional validada, búsqueda por texto/voz, accesibilidad, códigos QR, rutas internas y un panel de administración por áreas.

<p align="center">
  <img src="https://img.shields.io/badge/Estado-V2%20Operativa-success?style=for-the-badge" alt="Estado">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-Producción-4169E1?style=for-the-badge&logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Tests-pytest-yellow?style=for-the-badge&logo=pytest" alt="Tests">
  <img src="https://img.shields.io/badge/Open%20Source-Sin%20costo%20de%20licencia-2ea44f?style=for-the-badge" alt="Open Source">
</p>

<p align="center">
  <strong>🔎 Buscar · 🎙️ Hablar · ♿ Acceder · 📍 Orientarse · 📞 Solicitar ayuda · 📊 Mejorar</strong>
</p>

---

## 📌 Repositorio

**GitHub:**  
https://github.com/edergc/JustiOrienta

Para obtener el código:

```bash
git clone https://github.com/edergc/JustiOrienta.git
cd JustiOrienta
```

> Este README está pensado para que **otro profesional de Informática pueda clonar, configurar PostgreSQL, ejecutar migraciones, cargar datos, probar el sistema y dejarlo funcionando**, sin tener que conocer previamente el proyecto.

---

# 📖 Índice

- [1. ¿Qué es Justicia Orienta?](#1--qué-es-justicia-orienta)
- [2. Funcionalidades](#2--funcionalidades)
- [3. Arquitectura](#3--arquitectura)
- [4. Requisitos](#4--requisitos)
- [5. Instalación rápida para pruebas](#5--instalación-rápida-para-pruebas)
- [6. Instalación recomendada con PostgreSQL](#6--instalación-recomendada-con-postgresql)
- [7. Configuración de `.env`](#7--configuración-de-env)
- [8. Crear y preparar la base de datos](#8--crear-y-preparar-la-base-de-datos)
- [9. Ejecutar migraciones](#9--ejecutar-migraciones)
- [10. Crear administrador inicial](#10--crear-administrador-inicial)
- [11. Cargar el catálogo institucional](#11--cargar-el-catálogo-institucional)
- [12. Ejecutar la aplicación](#12--ejecutar-la-aplicación)
- [13. Acceso desde otra PC de la LAN](#13--acceso-desde-otra-pc-de-la-lan)
- [14. Crear un servicio en Windows Server](#14--crear-un-servicio-en-windows-server)
- [15. Pruebas y validación](#15--pruebas-y-validación)
- [16. Prueba funcional completa](#16--prueba-funcional-completa)
- [17. Roles y flujo editorial](#17--roles-y-flujo-editorial)
- [18. Base de datos y migraciones futuras](#18--base-de-datos-y-migraciones-futuras)
- [19. Respaldos y restauración](#19--respaldos-y-restauración)
- [20. Logs y diagnóstico](#20--logs-y-diagnóstico)
- [21. Despliegue en Render](#21--despliegue-en-render)
- [22. Seguridad](#22--seguridad)
- [23. Estructura del proyecto](#23--estructura-del-proyecto)
- [24. Datos institucionales](#24--datos-institucionales)
- [25. CI/CD](#25--cicd)
- [26. Solución de problemas](#26--solución-de-problemas)
- [27. Roadmap](#27--roadmap)
- [28. Principios](#28--principios)

---

# 1. 🌟 ¿Qué es Justicia Orienta?

**Justicia Orienta** es un orientador ciudadano accesible para la **Corte Superior de Justicia de Lima**.

Permite que una persona pueda realizar preguntas como:

```text
"¿Dónde está el Juzgado de Familia?"

"Necesito presentar una demanda de alimentos"

"¿Dónde pago una multa?"

"¿Hay ascensor?"

"¿Cómo llego al 11.º Juzgado Civil?"

"No encuentro la oficina que necesito"
```

El sistema busca la información dentro de un **catálogo institucional validado**.

Si existe información suficiente, muestra la dependencia, sede, ubicación, servicios y demás información disponible.

Si no existe certeza:

> **El sistema no inventa una respuesta.**

En ese caso orienta al ciudadano hacia un canal de atención humana.

---

# 2. ✨ Funcionalidades

## 👤 Para la ciudadanía

| Funcionalidad | Descripción |
|---|---|
| 🔎 Búsqueda | Texto y lenguaje natural. |
| 🎙️ Voz | Reconocimiento de habla del navegador. |
| ♿ Accesibilidad | Alto contraste, texto ampliable, tema oscuro y lectura en voz alta. |
| 📍 Ubicación | Sede, edificio, piso y dependencia. |
| 🧭 Wayfinding | Ruta interna paso a paso. |
| ♿ Ruta accesible | Evita tramos no accesibles cuando el mapa está configurado. |
| 📱 QR | Acceso directo desde carteles físicos. |
| 📞 Atención | Solicitar que la institución llame o escriba. |
| 📄 PDF | Directorio descargable e imprimible. |
| 👍 Satisfacción | Evaluación de utilidad de la consulta. |

## 🏢 Para las áreas de la Corte

| Funcionalidad | Descripción |
|---|---|
| 👥 Usuarios | Gestión de usuarios y roles. |
| 🗂️ Dependencias | Crear y actualizar información del área. |
| 🏢 Sedes | Administración de sedes. |
| 🏬 Edificios | Administración de edificios. |
| 🧾 Servicios | Requisitos, canales y horarios. |
| ✅ Validación | Flujo revisión → aprobación. |
| 🧭 Mapa interno | Nodos y conexiones. |
| 📊 Indicadores | Métricas de uso y calidad del catálogo. |
| 🧾 Auditoría | Registro de acciones. |
| 📥 Excel | Importación/exportación. |
| 📱 QR | Generación local de códigos QR. |

---

# 3. 🏗️ Arquitectura

La aplicación actual funciona como un **monolito web sencillo de desplegar**:

```text
                        CIUDADANÍA
                            │
              ┌─────────────┴─────────────┐
              │                           │
           🌐 Web                      📱 QR
              │                           │
              └─────────────┬─────────────┘
                            │
                            ▼
                 ┌────────────────────┐
                 │  Justicia Orienta  │
                 │ FastAPI + HTML/CSS │
                 │       + JS         │
                 └─────────┬──────────┘
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
          🔎 NLP       🧭 Rutas       📞 Atención
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │    PostgreSQL      │
                 │                    │
                 │ Sedes              │
                 │ Dependencias       │
                 │ Servicios          │
                 │ Usuarios           │
                 │ Auditoría          │
                 │ Métricas           │
                 │ Wayfinding         │
                 └────────────────────┘
                           ▲
                           │
                 ┌─────────┴─────────┐
                 │     /admin        │
                 │                   │
                 │ Gestión            │
                 │ Validación         │
                 │ Usuarios           │
                 │ Auditoría          │
                 │ Indicadores        │
                 │ Mapa interno       │
                 └───────────────────┘
```

### Importante

No hay que levantar por separado un frontend React/Vite y un backend.

La versión actual sirve:

```text
Sitio público
Panel administrativo
API
```

desde el mismo proceso FastAPI y el mismo puerto. citeturn1view0

---

# 4. 🧰 Requisitos

## Software

### Obligatorio

- Git
- Python **3.10 o superior**
- pip
- PostgreSQL **para instalación recomendada/producción**
- Cliente PostgreSQL (`psql`, `pg_dump`, `pg_restore`) para administración y respaldos

### No es necesario

Para la versión actual **no es necesario instalar**:

- Node.js
- npm
- React
- Vite
- Docker
- Redis
- Nginx para una prueba local
- servicios de IA externos

Las dependencias Python reales se encuentran en `requirements.txt`. citeturn2view2

---

# 5. 🚀 Instalación rápida para pruebas

Esta opción permite probar el sistema sin instalar PostgreSQL.

La plantilla `.env.example` utiliza SQLite como configuración de cero instalación. citeturn2view1

## 5.1 Clonar

```bash
git clone https://github.com/edergc/JustiOrienta.git
cd JustiOrienta
```

## 5.2 Crear entorno virtual

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 5.3 Actualizar pip

```bash
python -m pip install --upgrade pip
```

## 5.4 Instalar dependencias

```bash
pip install -r requirements.txt
```

## 5.5 Crear `.env`

### Windows

```powershell
Copy-Item .env.example .env
```

### Linux

```bash
cp .env.example .env
```

Para una prueba rápida puede mantenerse:

```env
ENTORNO=desarrollo
DATABASE_URL=sqlite:///./justicia_orienta.db
```

## 5.6 Crear tablas

```bash
python -m alembic upgrade head
```

## 5.7 Crear administrador

```bash
python -m app.seed
```

## 5.8 Cargar catálogo

```bash
python -m app.cargar_directorio_pj
```

## 5.9 Ejecutar

```bash
python run.py
```

Abrir:

```text
http://127.0.0.1:8743/
```

Administración:

```text
http://127.0.0.1:8743/admin
```

API:

```text
http://127.0.0.1:8743/api/docs
```

Estos son los comandos de bootstrap que utiliza actualmente el proyecto. citeturn1view0

---

# 6. 🐘 Instalación recomendada con PostgreSQL

> **Esta es la instalación recomendada para un servidor institucional o entorno de producción.**

La aplicación está preparada para PostgreSQL mediante `DATABASE_URL`. El repositorio indica PostgreSQL como base de datos del entorno real. citeturn1view0

La arquitectura recomendada es:

```text
┌───────────────────────┐
│ PC / Servidor Windows│
│                       │
│ Justicia Orienta     │
│ Python + FastAPI     │
│ Puerto 8743           │
└───────────┬───────────┘
            │
            │ TCP 5432
            ▼
┌───────────────────────┐
│ PostgreSQL            │
│                       │
│ justicia_orienta      │
└───────────────────────┘
```

PostgreSQL puede estar:

1. En el mismo servidor de la aplicación.
2. En otro servidor de base de datos.
3. En una instancia administrada compatible con PostgreSQL.

---

# 7. ⚙️ Configuración de `.env`

Copiar:

```text
.env.example
```

a:

```text
.env
```

La plantilla actual define estas variables principales: `ENTORNO`, `DATABASE_URL`, `JUSTICIA_ORIENTA_SECRET`, `URL_PUBLICA` y las variables SMTP. citeturn2view1

## Ejemplo de desarrollo con PostgreSQL

```env
ENTORNO=desarrollo

DATABASE_URL=postgresql+psycopg2://justicia_app:CLAVE@localhost:5432/justicia_orienta

JUSTICIA_ORIENTA_SECRET=CAMBIAR_POR_UN_SECRETO_LARGO_Y_ALEATORIO

URL_PUBLICA=http://localhost:8743

SMTP_HOST=
SMTP_PORT=587
SMTP_USUARIO=
SMTP_PASSWORD=
SMTP_REMITENTE=Justicia Orienta <no-responder@justiciaorienta.local>
```

## Producción

```env
ENTORNO=produccion

DATABASE_URL=postgresql+psycopg2://justicia_app:CLAVE@SERVIDOR_POSTGRES:5432/justicia_orienta

JUSTICIA_ORIENTA_SECRET=SECRETO_UNICO_Y_SEGURO

URL_PUBLICA=https://dominio.institucional.gob.pe
```

> 🔐 **Nunca publiques el `.env` ni una contraseña de PostgreSQL en GitHub.**

El proyecto está preparado para negarse a iniciar en producción si continúa el secreto de ejemplo. citeturn1view1

---

# 8. 🗄️ Crear y preparar la base de datos

## 8.1 Opción A — PostgreSQL instalado en Windows

Abrir **SQL Shell (psql)** o una terminal con `psql`.

Conectarse como administrador:

```bash
psql -U postgres
```

Crear usuario:

```sql
CREATE USER justicia_app WITH PASSWORD 'CAMBIAR_ESTA_CLAVE';
```

Crear base de datos:

```sql
CREATE DATABASE justicia_orienta
    OWNER justicia_app;
```

Salir:

```sql
\q
```

## 8.2 Probar conexión

```bash
psql -h localhost -U justicia_app -d justicia_orienta
```

Si solicita contraseña y permite entrar:

```text
justicia_orienta=>
```

la conexión funciona.

Salir:

```sql
\q
```

---

## 8.3 Si PostgreSQL está en otro servidor

Por ejemplo:

```text
Servidor aplicación: 172.20.1.51
Servidor PostgreSQL: 172.20.1.52
Puerto PostgreSQL:   5432
Base:                justicia_orienta
Usuario:             justicia_app
```

El `.env` sería:

```env
DATABASE_URL=postgresql+psycopg2://justicia_app:CLAVE@172.20.1.52:5432/justicia_orienta
```

Además, el administrador de PostgreSQL debe permitir conexiones desde el servidor de aplicación mediante:

```text
pg_hba.conf
```

y PostgreSQL debe estar escuchando en la interfaz correspondiente mediante:

```text
postgresql.conf
```

Finalmente debe existir conectividad TCP al puerto:

```text
5432
```

---

# 9. 🔄 Ejecutar migraciones

Una vez configurado correctamente `DATABASE_URL`:

```bash
python -m alembic upgrade head
```

Esto crea/actualiza la estructura de tablas de la aplicación.

### Verificar

```bash
alembic current
```

También puede comprobarse directamente desde PostgreSQL:

```sql
\dt
```

Debe aparecer el conjunto de tablas generado por las migraciones.

### Regla importante

**No crear manualmente las tablas de la aplicación.**

La estructura debe ser administrada mediante:

```text
Alembic
   ↓
migrations/
   ↓
python -m alembic upgrade head
```

---

# 10. 👑 Crear administrador inicial

Ejecutar:

```bash
python -m app.seed
```

El script crea el usuario administrador inicial.

Luego entrar en:

```text
http://127.0.0.1:8743/admin
```

El sistema obliga a cambiar la contraseña inicial antes de continuar.

El acceso administrativo utiliza DNI de 8 dígitos y la aplicación bloquea una cuenta después de 5 intentos fallidos consecutivos durante 15 minutos. citeturn1view0

---

# 11. 📚 Cargar el catálogo institucional

Existen varias formas de cargar información.

## Opción A — Directorio oficial

```bash
python -m app.cargar_directorio_pj
```

El cargador extrae información del directorio institucional y evita duplicar registros cuando vuelve a ejecutarse. citeturn1view1

## Opción B — Excel

```bash
python -m app.import_excel "archivo.xlsx"
```

## Opción C — Datos del repositorio

El repositorio también contiene archivos Excel utilizados por los procesos de carga de producción:

```text
DirectorioCSJLI.xlsx
ConformacionCSJLima.xlsx
```

y `render.yaml` define comandos específicos para cargarlos durante el despliegue en Render. citeturn1view1

> ⚠️ La carga de datos y la publicación son conceptos diferentes. La información puede quedar en `revision` hasta que sea validada por el área correspondiente.

---

# 12. ▶️ Ejecutar la aplicación

## Desarrollo

```bash
python run.py
```

Por defecto:

```text
http://127.0.0.1:8743/
```

### Sitio público

```text
http://127.0.0.1:8743/
```

### Administración

```text
http://127.0.0.1:8743/admin
```

### Swagger / API

```text
http://127.0.0.1:8743/api/docs
```

---

# 13. 🌐 Acceso desde otra PC de la LAN

Si se desea que otros equipos de la red institucional puedan probar la aplicación:

## 13.1 Escuchar en todas las interfaces

En lugar de:

```text
127.0.0.1
```

la aplicación debe escuchar:

```text
0.0.0.0
```

Por ejemplo:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8743
```

o utilizar el mecanismo de arranque previsto por el proyecto.

## 13.2 Identificar IP del servidor

Windows:

```powershell
ipconfig
```

Ejemplo:

```text
IPv4: 172.20.1.51
```

## 13.3 Probar desde otro equipo

En el navegador:

```text
http://172.20.1.51:8743/
```

Administración:

```text
http://172.20.1.51:8743/admin
```

API:

```text
http://172.20.1.51:8743/api/docs
```

## 13.4 Firewall de Windows

Si Windows Firewall bloquea el puerto, crear una regla de entrada:

```powershell
New-NetFirewallRule `
  -DisplayName "Justicia Orienta - TCP 8743" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 8743 `
  -Action Allow
```

> 🔐 En una red institucional, se recomienda restringir la regla a las subredes necesarias en lugar de abrir el puerto indiscriminadamente.

---

# 14. 🖥️ Crear un servicio en Windows Server

Para un servidor institucional, **no es recomendable depender de una consola abierta**.

La aplicación debe ejecutarse como servicio o mediante un mecanismo equivalente de supervisión.

Una alternativa práctica es **NSSM (Non-Sucking Service Manager)** o el mecanismo institucional de servicios.

## Parámetros

Programa:

```text
C:\JusticiaOrienta\.venv\Scripts\python.exe
```

Argumentos:

```text
-m uvicorn app.main:app --host 0.0.0.0 --port 8743
```

Directorio:

```text
C:\JusticiaOrienta
```

Variables de entorno:

```text
DATABASE_URL=...
ENTORNO=produccion
JUSTICIA_ORIENTA_SECRET=...
```

### Antes de convertirlo en servicio

Primero comprobar manualmente:

```powershell
cd C:\JusticiaOrienta
.\.venv\Scripts\Activate.ps1

python -m alembic upgrade head
python -m app.seed
python run.py
```

Solo cuando funcione correctamente se recomienda convertirlo en servicio.

---

# 15. 🧪 Pruebas y validación

## 15.1 Ejecutar toda la suite

```bash
python -m pytest
```

La suite cubre buscador, permisos, autenticación, wayfinding, solicitudes, sedes, servicios, indicadores, exportaciones y accesibilidad. El repositorio declara actualmente **158 pruebas**. citeturn1view0

## 15.2 Ejecutar pruebas con información detallada

```bash
python -m pytest -v
```

## 15.3 Ejecutar una prueba específica

```bash
python -m pytest tests/ -k "buscar"
```

## 15.4 Auditoría de accesibilidad

```bash
python -m app.auditoria_accesibilidad
```

Esta auditoría verifica aspectos estáticos del HTML; no reemplaza una evaluación real con lector de pantalla ni una revisión visual de contraste. citeturn1view0

---

# 16. 🧪 Prueba funcional completa

Después del despliegue, realizar esta secuencia.

## A. Prueba técnica

```text
[ ] PostgreSQL responde
[ ] DATABASE_URL funciona
[ ] Alembic terminó correctamente
[ ] Aplicación inicia
[ ] Puerto 8743 responde
[ ] /api/docs responde
[ ] Logs no muestran errores críticos
```

## B. Prueba ciudadana

```text
[ ] Página principal abre
[ ] Buscador funciona
[ ] Búsqueda por voz funciona en navegador compatible
[ ] Resultado muestra información
[ ] Lectura en voz alta funciona
[ ] Alto contraste funciona
[ ] Texto ampliable funciona
[ ] Tema oscuro funciona
[ ] QR abre la página
[ ] PDF puede descargarse
```

## C. Prueba administrativa

```text
[ ] /admin abre
[ ] Login funciona
[ ] Cambio obligatorio de contraseña funciona
[ ] Usuario gestor puede editar su área
[ ] Gestor no puede publicar directamente
[ ] Validador puede aprobar
[ ] Información aprobada aparece en público
[ ] Auditoría registra las acciones
```

## D. Prueba de base de datos

```text
[ ] Crear dependencia
[ ] Editar dependencia
[ ] Aprobar dependencia
[ ] Crear servicio
[ ] Desactivar servicio
[ ] Reactivar servicio
[ ] Exportar Excel
[ ] Importar Excel
[ ] Generar QR
[ ] Generar reporte
```

---

# 17. 👥 Roles y flujo editorial

| Rol | Funciones |
|---|---|
| 👑 **admin** | Administración completa. |
| ✏️ **gestor** | Crear/editar contenido de su área. |
| ✅ **validador** | Revisar, aprobar o devolver contenido de su área. |
| 🔍 **auditor** | Consultar auditoría e indicadores. |
| 📊 **consulta** | Consulta de indicadores y auditoría. |

Flujo:

```text
              Área registra información
                       │
                       ▼
                 🟡 REVISIÓN
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
         ❌ DEVOLVER         ✅ APROBAR
              │                 │
              │                 ▼
              └────────────► 🟢 ACTIVO
                                │
                                ▼
                         🌎 CIUDADANÍA
```

La regla es:

> **Guardar información no significa publicarla.**

El contenido debe pasar por validación antes de aparecer al ciudadano. citeturn1view0

---

# 18. 🗄️ Base de datos y migraciones futuras

Cuando se modifica un modelo en:

```text
app/models/
```

no se debe modificar directamente la estructura de producción.

Crear una migración:

```bash
python -m alembic revision --autogenerate -m "descripcion del cambio"
```

Revisar el archivo generado y luego ejecutar:

```bash
python -m alembic upgrade head
```

Flujo recomendado:

```text
Modificar modelo
       │
       ▼
Generar migración
       │
       ▼
Revisar migración
       │
       ▼
Probar localmente
       │
       ▼
pytest
       │
       ▼
Git commit
       │
       ▼
Producción
       │
       ▼
alembic upgrade head
```

---

# 19. 💾 Respaldos y restauración

## Crear respaldo

```bash
python backup_db.py
```

Para PostgreSQL utiliza `pg_dump` en formato comprimido.

El proyecto mantiene respaldos con fecha/hora y aplica una retención configurable. citeturn1view0

## Restaurar PostgreSQL

Primero crear la base si no existe:

```bash
createdb -U postgres justicia_orienta
```

Luego:

```bash
pg_restore \
  -h localhost \
  -U justicia_app \
  -d justicia_orienta \
  backups/justicia_orienta_YYYYMMDD_HHMMSS.dump
```

En Windows PowerShell puede utilizarse:

```powershell
pg_restore `
  -h localhost `
  -U justicia_app `
  -d justicia_orienta `
  .\backups\justicia_orienta_YYYYMMDD_HHMMSS.dump
```

Después:

```bash
python -m alembic upgrade head
```

> ⚠️ Restaurar una base de producción debe realizarse como operación controlada. Verificar primero que el destino sea realmente la base que se desea sobrescribir.

---

# 20. 📋 Logs y diagnóstico

Los errores de aplicación se registran en:

```text
logs/justicia_orienta.log
```

El sistema mantiene rotación automática de logs. citeturn1view1

## Si la aplicación no inicia

Ejecutar directamente:

```bash
python run.py
```

y observar el error.

## Si falla PostgreSQL

Probar:

```bash
psql -h HOST -U justicia_app -d justicia_orienta
```

## Si falla Alembic

Ejecutar:

```bash
alembic current
alembic heads
python -m alembic upgrade head
```

## Si el puerto está ocupado en Windows

```powershell
netstat -ano | findstr :8743
```

Luego identificar el proceso:

```powershell
tasklist /FI "PID eq NUMERO_PID"
```

---

# 21. ☁️ Despliegue en Render

El repositorio ya incluye:

```text
render.yaml
```

y actualmente define un servicio Python que:

1. Instala dependencias.
2. Ejecuta migraciones.
3. Crea/actualiza el administrador.
4. Carga datos.
5. Inicia Uvicorn.

El `render.yaml` del repositorio define actualmente `python 3.12.7`, `ENTORNO=produccion` y solicita configurar `DATABASE_URL`, `URL_PUBLICA` y SMTP como variables externas. citeturn2view0

## 21.1 Crear una base PostgreSQL

Se necesita una base PostgreSQL accesible desde Render.

Puede ser:

- PostgreSQL administrado.
- Neon u otro proveedor PostgreSQL compatible.
- Una base institucional accesible desde Internet, si la política de seguridad lo permite.

La cadena debe tener el formato:

```text
postgresql+psycopg2://usuario:clave@host/basededatos?sslmode=require
```

El propio `render.yaml` contempla esta modalidad. citeturn2view0

## 21.2 Crear Web Service

En Render:

```text
New
  ↓
Web Service
  ↓
Conectar GitHub
  ↓
edergc/JustiOrienta
```

## 21.3 Configuración

El repositorio ya contiene:

```text
render.yaml
```

por lo que puede utilizarse la configuración definida allí.

## 21.4 Variables obligatorias

Configurar en Render:

```text
DATABASE_URL
JUSTICIA_ORIENTA_SECRET
URL_PUBLICA
```

Para recuperación de contraseña por correo:

```text
SMTP_HOST
SMTP_PORT
SMTP_USUARIO
SMTP_PASSWORD
SMTP_REMITENTE
```

El archivo `render.yaml` marca estas variables como valores que deben introducirse fuera del repositorio. citeturn2view0

## 21.5 Después del despliegue

Probar:

```text
https://TU-DOMINIO/
https://TU-DOMINIO/admin
https://TU-DOMINIO/api/docs
```

Y ejecutar la misma matriz de pruebas funcionales descrita en este README.

---

# 22. 🔐 Seguridad

La aplicación incluye controles como:

- Contraseñas con bcrypt.
- Bloqueo después de intentos fallidos.
- Rate limiting.
- Cabeceras HTTP de seguridad.
- Escape de contenido HTML.
- Protección contra inyección de fórmulas en Excel.
- Auditoría de acciones.
- Registro de IP.
- Secreto obligatorio en producción.
- Separación de permisos por rol y área.

Estos controles están implementados en el código actual del repositorio. citeturn1view1

## HTTPS

Para producción pública:

```text
Internet
   │
   ▼
HTTPS / TLS
   │
   ▼
Proxy / Balanceador
   │
   ▼
Justicia Orienta
   │
   ▼
PostgreSQL
```

El piloto local utiliza HTTP, pero una publicación institucional debe utilizar HTTPS. citeturn1view1

---

# 23. 📁 Estructura del proyecto

```text
JustiOrienta/
│
├── .github/
│   └── workflows/
│
├── app/
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   ├── nlp.py
│   ├── main.py
│   ├── rate_limit.py
│   ├── rutas_internas.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── crud/
│   ├── routers/
│   └── static/
│
├── migrations/
├── fuentes/
├── tests/
├── prototipo-v1/
│
├── backups/
├── logs/
│
├── .env.example
├── .gitignore
├── alembic.ini
├── backup_db.py
├── requirements.txt
├── run.py
├── render.yaml
│
├── DirectorioCSJLI.xlsx
├── ConformacionCSJLima.xlsx
└── README.md
```

---

# 24. 📚 Datos institucionales

El proyecto utiliza información institucional como fuente del catálogo.

El repositorio incluye el directorio oficial utilizado por el proceso de carga. La aplicación documenta que el catálogo fue cargado a partir del directorio oficial de la CSJ Lima y que la información adicional debe ser revisada por las áreas responsables. citeturn1view1

## Regla de calidad

El sistema distingue:

```text
Fuente
  │
  ▼
Carga
  │
  ▼
Revisión
  │
  ▼
Aprobación
  │
  ▼
Publicación
```

No debe asumirse que una carga masiva equivale a una validación institucional.

---

# 25. 🔄 CI/CD

El repositorio dispone de GitHub Actions:

```text
.github/workflows/
```

Cada `push` y Pull Request hacia `master` ejecuta las pruebas automatizadas. citeturn1view1

Flujo:

```text
Developer
    │
    ▼
git push
    │
    ▼
GitHub
    │
    ▼
GitHub Actions
    │
    ▼
pytest
    │
 ┌──┴──┐
 ▼     ▼
✅    ❌
OK    Error
```

---

# 26. 🛠️ Solución de problemas

## ❌ `ModuleNotFoundError`

Verificar que el entorno virtual esté activo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Luego:

```bash
pip install -r requirements.txt
```

---

## ❌ `connection refused` a PostgreSQL

Comprobar:

```text
Servidor PostgreSQL
Puerto 5432
Usuario
Contraseña
Base de datos
Firewall
pg_hba.conf
postgresql.conf
```

Y probar:

```bash
psql -h HOST -U justicia_app -d justicia_orienta
```

---

## ❌ `password authentication failed`

La contraseña de PostgreSQL no coincide con la utilizada en:

```env
DATABASE_URL=...
```

Restablecer la contraseña del usuario PostgreSQL y actualizar `.env`.

---

## ❌ `database "justicia_orienta" does not exist`

Crear:

```sql
CREATE DATABASE justicia_orienta
    OWNER justicia_app;
```

---

## ❌ `alembic upgrade head` falla

Primero verificar:

```bash
alembic current
alembic heads
```

y comprobar que `DATABASE_URL` apunta a la base correcta.

---

## ❌ El sistema funciona en `localhost` pero no desde otra PC

Comprobar:

```text
1. Uvicorn escucha en 0.0.0.0
2. Puerto 8743
3. Firewall Windows
4. Conectividad de red
5. IP correcta del servidor
```

Probar desde el cliente:

```powershell
Test-NetConnection 172.20.1.51 -Port 8743
```

---

## ❌ El sitio abre pero no hay información

Ejecutar:

```bash
python -m app.cargar_directorio_pj
```

o cargar un Excel:

```bash
python -m app.import_excel "archivo.xlsx"
```

Después revisar:

```text
/admin
```

y comprobar el estado de los registros.

---

## ❌ Los datos existen pero no aparecen públicamente

Revisar el estado editorial.

La aplicación publica únicamente contenido aprobado/activo; el flujo de revisión y aprobación está implementado deliberadamente. citeturn1view0

---

# 27. 🛣️ Roadmap

| Versión | Evolución | Estado |
|---|---|---|
| **V0** | Protocolo humano + catálogo | 🟢 Diseñado |
| **V1** | Micrositio estático | 🟢 Completado |
| **V2** | Backend + PostgreSQL + panel + roles | 🟢 Completado |
| **V3** | Lenguaje natural | 🟢 Completado |
| **V4** | Mapa interno + rutas | 🟢 Completado |
| **V5** | Integraciones institucionales | 🔵 Futuro |
| **V6** | Evolución de orientación conversacional | 🔵 Futuro |

La interpretación actual del lenguaje natural utiliza reglas explícitas y auditables, no un modelo generativo de IA. citeturn1view1

---

# 28. 🏛️ Principios

## 🚫 1. Nunca inventar información institucional

Si el sistema no tiene certeza:

```text
NO ADIVINA
    ↓
INFORMA LA LIMITACIÓN
    ↓
DERIVA A ATENCIÓN HUMANA
```

## 🏢 2. Cada área es responsable de su información

Informática administra la plataforma.

Las áreas son responsables de mantener y validar su contenido.

## 👀 3. Nadie se autopublica

```text
Guardar ≠ Publicar
```

## ♿ 4. Accesibilidad desde el inicio

No es una característica para una versión futura.

## 🧾 5. Todo debe poder auditarse

La plataforma registra las operaciones relevantes.

## 📚 6. La información debe tener una fuente

```text
Fuente
  ↓
Dato
  ↓
Revisión
  ↓
Validación
  ↓
Publicación
```

---

# 🏁 Checklist de instalación para otro informático

Un administrador que reciba el repositorio debería poder seguir esta lista:

```text
☐ 1. Instalar Git
☐ 2. Instalar Python 3.10+
☐ 3. Instalar PostgreSQL
☐ 4. Crear usuario justicia_app
☐ 5. Crear BD justicia_orienta
☐ 6. Clonar https://github.com/edergc/JustiOrienta.git
☐ 7. Crear .venv
☐ 8. Activar .venv
☐ 9. pip install -r requirements.txt
☐ 10. Crear .env
☐ 11. Configurar DATABASE_URL
☐ 12. Configurar JUSTICIA_ORIENTA_SECRET
☐ 13. Ejecutar alembic upgrade head
☐ 14. Ejecutar app.seed
☐ 15. Cargar catálogo
☐ 16. Ejecutar pytest
☐ 17. Ejecutar auditoría de accesibilidad
☐ 18. Ejecutar python run.py
☐ 19. Probar / 
☐ 20. Probar /admin
☐ 21. Probar /api/docs
☐ 22. Probar desde otra PC de la LAN
☐ 23. Configurar firewall si corresponde
☐ 24. Configurar servicio Windows si será servidor
☐ 25. Configurar backups
☐ 26. Validar flujo gestor → validador → ciudadano
☐ 27. Documentar IP, puerto y credenciales institucionales
☐ 28. Si es público: HTTPS + dominio + infraestructura institucional
```

---

# ⭐ Resumen para TI

La instalación recomendada queda así:

```text
                  ┌──────────────────────────┐
                  │       CLIENTES LAN       │
                  │ PCs / tablets / móviles  │
                  └────────────┬─────────────┘
                               │
                         TCP 8743 / HTTPS
                               │
                               ▼
                  ┌──────────────────────────┐
                  │     SERVIDOR WEB         │
                  │                          │
                  │ Justicia Orienta         │
                  │ Python + FastAPI         │
                  │                          │
                  │ 0.0.0.0:8743             │
                  └────────────┬─────────────┘
                               │
                         TCP 5432
                               │
                               ▼
                  ┌──────────────────────────┐
                  │       PostgreSQL         │
                  │                          │
                  │ justicia_orienta         │
                  └──────────────────────────┘
```

Con esto, un nuevo integrante de Informática puede pasar de:

```text
Repositorio GitHub
        ↓
Clonar
        ↓
Python + entorno virtual
        ↓
PostgreSQL
        ↓
.env
        ↓
Alembic
        ↓
Seed
        ↓
Carga de catálogo
        ↓
Pruebas
        ↓
Servidor
        ↓
LAN
        ↓
Servicio
        ↓
Backups
        ↓
Producción
```

sin necesidad de conocer previamente la arquitectura interna del proyecto.

---

<p align="center">

# ⚖️ Justicia Orienta

<strong>Orientación ciudadana · Accesibilidad · Información validada · Innovación · Mejora continua</strong>

<br><br>

<em>“Que encontrar la justicia sea también fácil de encontrar.”</em>

</p>
