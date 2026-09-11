# Proyecto Maestro: Justicia Orienta
### Modelo Integral de Orientación y Atención al Ciudadano — Corte Superior de Justicia de Lima

**Versión 2.0 — Edición verificada contra el sistema real**
**Fecha de corte:** 25 de agosto de 2026
**Parte de:** `ProyectoJusticia.doc` (v1.0, mismo día) — este documento lo hereda, pero corrige cada afirmación contra el código y la base de datos en producción, no contra lo planeado en papel.

> *"No necesitas conocer la Corte. Justicia Orienta te guía."*

---

## 0. Por qué existe esta versión 2.0

El documento original (`ProyectoJusticia.doc`, 41 páginas) es un trabajo sólido: visión clara, matriz de brechas de 32 puntos, arquitectura en capas, modelo de gobernanza con 17 áreas, matriz de 54 funcionalidades, calendario en 3 fases. Pero se escribió sin cruzar cada afirmación contra el sistema que ya corre en producción — y varias ya no son ciertas, en ambos sentidos: cosas que decía "no existen" y sí existen, y compromisos que decía "pendientes" y ya están cumplidos con creces.

Esta edición corrige eso. Cada casilla ✅/⚠️/❌ de aquí en adelante fue verificada leyendo el código real (modelos, rutas, paneles) o consultando la base de datos de producción el 25 de agosto de 2026, no copiada del plan original.

**Correcciones más importantes encontradas:**

| # | El documento original decía | La verificación encontró |
|---|---|---|
| 1 | QR de acceso rápido: ❌ No existe | ✅ Ya existe — `app/routers/admin_qr.py` genera QR por sede y por dependencia, usado hoy en producción |
| 2 | Dashboard de métricas: ❌ Prototipo pendiente (ítem 1.11 del plan) | ✅ Ya existe y está visible en el panel admin — consultas totales, % resueltas, top búsquedas sin resultado, % por voz, % modo accesible, consultas por sede/área/tipo, completitud de datos, pendientes por área |
| 3 | Trazabilidad de orientación: ❌ No existe | ✅ Botón "Historial" por dependencia en el panel: une auditoría (quién/cuándo/qué cambió) y `ConsultaLog` (cuántas veces se usó como respuesta, cuándo fue la última) en una sola vista |
| 4 | Carga de "20+ dependencias" pendiente | ✅ Superado: **505 dependencias reales en 26 sedes** ya cargadas desde el directorio oficial de la Corte |
| 5 | Titulares (jueces/vocales/jefaturas) | No estaba contemplado en el documento original — hoy hay **73 titulares reales** cargados desde el reporte oficial de Conformación, en la sede piloto |
| 6 | Botón "Cómo llegar (Google Maps)" | Es OpenStreetMap, no Google Maps — mismo efecto, sin depender de una cuenta de Google ni su facturación |
| 7 | Base de datos | Hoy corre en **PostgreSQL persistente (Neon)**, no en SQLite de prueba — sobrevive reinicios y redeploys. Revisión de estructura (31 ago): corregido el enum `rol` (faltaba el valor "consulta" en el tipo real de Postgres — creaba un error crudo de base de datos al usar ese rol), agregado `pool_pre_ping` (evita fallos tras cortes de conexión de Neon), e indices/llaves foráneas completados (`dependencias.edificio_id`, índice compuesto de `auditoria`, FK real de `consulta_log`) |
| 8 | Manuales de usuario y administración | Ya existen y están terminados: `JusticiaOrienta_06_Manual_Panel_Administracion.docx` y `_07_Manual_Ciudadano.docx` |
| 9 | Replicabilidad: ❌ No documentada | Ya **demostrada en la práctica**: las 26 sedes se cargaron sin tocar una línea de código, solo important su propio directorio — falta documentarla como manual formal, no probarla |

Nada de esto invalida el trabajo original — al contrario, confirma que el proyecto avanzó más rápido de lo que el propio plan anticipaba. Esta versión simplemente pone el marcador al día antes de comprometer un calendario nuevo.

---

## 0.1 Actualización — 27 de agosto de 2026

En los dos días siguientes al corte de la versión 2.0 se construyó, se probó y se desplegó a producción lo siguiente — parte de esto ya estaba en la lista de Fase 4 (§5); otra parte no estaba contemplada en ningún plan anterior:

- **Rediseño completo del panel de administración**: barra lateral con Dashboard propio (indicador destacado de "primera orientación correcta" con barra de progreso, mini-gráficos por ranking), navegación agrupada por Catálogo/Control, y pantalla de inicio de sesión con fotografía real de la sede piloto.
- **Restablecer contraseña por correo**: cada usuario del panel puede pedir un enlace a su correo registrado para elegir una nueva contraseña sin depender de un(a) administrador(a) — token de un solo uso, vence en 30 minutos, con límite de intentos por DNI e IP para evitar abuso.
- **Mapa interno (wayfinding), Fase 4 §5 ítem 2 y §6.3**: grafo de nodos y conexiones con ruta más corta (Dijkstra, sin librerías externas) para el Nivel 1 de la Sede Javier Alzamora Valdez, extraído de los planos reales del edificio (BIM del Ex Ministerio de Educación, arq. Enrique Seoane Ros, 1956). Incluye un **mapa visual interactivo** (diagrama esquemático propio, no una copia de ningún plano de terceros) con la ruta dibujada sobre la planta real, y un diagrama genérico de "planta típica" para los pisos 4 al 20 (mismo patrón documentado, sin oficina exacta marcada por falta de ese dato).
- **Corrección de relevancia del buscador**: buscar "1° Juzgado Constitucional" ya no mezclaba juzgados de otras especialidades (Familia, Trabajo, Civil) solo por compartir el número de orden.
- **32 pruebas automatizadas nuevas** cubriendo el mapa interno, el restablecimiento de contraseña, y el límite de intentos — nada de esto tenía cobertura antes del 27 de agosto.

De la tabla de Fase 4 (§5), estos ítems pasaron de "no existe" a construidos y en producción: **2** (parcial — falta fotografía por piso y ascensores en la ficha pública), **6**, **7**, **9** (documentado en `Metodologia_Medicion_Indicadores_JusticiaOrienta.docx`), **10**, **11**, **12** (documentado en `Politica_Proteccion_Datos_JusticiaOrienta.docx`), y **13**. El detalle de cada uno está marcado directamente en la tabla de §5.

---

## 1. Visión y filosofía (heredado, sin cambios)

**Concepto central:** Justicia Orienta es un modelo integral de buena práctica que transforma la experiencia del ciudadano en la Corte Superior de Justicia de Lima, guiándolo desde su necesidad hasta la resolución de su requerimiento, con enfoque en accesibilidad, inclusión y mejora continua.

**Los tres niveles de orientación:**

| Nivel | Pregunta del ciudadano | Qué resuelve | Estado real |
|---|---|---|---|
| 1. ¿Dónde? | "¿Dónde está el 11.º Juzgado Civil?" | Localización: sede, piso, anexo | ✅ Completo |
| 2. ¿Quién? | "¿Qué área ve mi caso?" | Área/titular responsable | ✅ Completo para jurisdiccional y ODECMA (73 titulares); pendiente para áreas administrativas |
| 3. ¿Cómo? | "¿Cómo hago este trámite?" | Requisitos, horario, ruta interna | ⚠️ Parcial — horario y requisitos existen como campos; ruta interna (`instrucciones_internas`) existe pero está vacía en casi todo el catálogo |

**Principios rectores** (sin cambios frente al original): ciudadano en el centro, accesibilidad universal, información validada, mejora continua, sostenibilidad, replicabilidad, transparencia.

---

## 2. Estado real verificado, por capa

### 2.1 Capa de experiencia ciudadana

| Funcionalidad | Estado real | Evidencia |
|---|---|---|
| Búsqueda por texto, tolerante a tildes y errores de tipeo | ✅ | `app/nlp.py`, `crud/busqueda.py` — probado: "informatika" encuentra "Coordinación de Informática" |
| Búsqueda por voz (Web Speech API) | ✅ | `public.js`, gratis, sin servidor de por medio |
| Lectura en voz alta de resultados | ✅ | `speechSynthesis`, incluye titular, anexo, accesibilidad, aviso de otra sede |
| Alto contraste / texto ampliable / tema oscuro / voz más lenta / Modo Adulto Mayor | ✅ | Persistido por visitante en `localStorage`; Modo Adulto Mayor (31 ago) combina texto al máximo tamaño, botones/campos/tarjetas ampliados y oculta la fila de "Ejemplos" para reducir ruido visual — se activa desde la barra de accesibilidad o automáticamente al elegir el perfil "Soy adulto mayor" |
| "No sé qué necesito" → deriva al módulo de orientación | ✅ | Tile en la portada, ya implementado |
| Aviso de "esta dependencia está en otra sede" + dirección | ✅ | Agregado esta semana |
| Titular a cargo (juez/a, vocal, jefe/a, coordinador/a) | ✅ | 73 reales cargados; campo listo para el resto |
| Ficha completa de sede (horario, accesibilidad, foto, todas sus dependencias en una sola vista) | ⚠️ | Vista única ("Estoy aquí"): dirección, horario, teléfono, accesibilidad y las dependencias de la sede agrupadas por piso, con enlace desde cualquier resultado de búsqueda y descarga del directorio de esa sede en PDF — falta fotografías de referencia (28 ago) |
| Ruta de atención de 3 niveles, completa | ⚠️ | Nivel 1 y 2 sólidos; nivel 3 (`instrucciones_internas`) es campo real pero vacío en casi todo el catálogo |
| Mapa interno de la sede | ❌ | Fuera de alcance a propósito (ver nota de diseño en el modelo: "nunca GPS/mapa indoor, eso no se promete") |
| Fotografías de referencia de sede/dependencia | ❌ | No existe |
| QR de acceso rápido por sede/dependencia | ✅ | Corrección — ya existe, `admin_qr.py` |
| Directorio descargable en PDF por sede | ✅ | `reportes_pdf.py` |
| Modo offline (PWA) | ✅ | `app/static/sw.js` + `manifest.json`, registrado en `public.js`, en producción desde el 27 ago |
| Kioscos de autoatención / tablet de orientador | ❌ | Es hardware físico, fuera del alcance de este repositorio |

### 2.2 Capa de gestión y administración

| Funcionalidad | Estado real |
|---|---|
| Panel de administración por área, con login propio (DNI + contraseña) | ✅ |
| Gestión de sedes, edificios, dependencias, servicios, alias | ✅ |
| Flujo de revisión y aprobación (gestor propone → validador de esa área aprueba) | ✅ |
| Auditoría de cada cambio (quién, cuándo, qué) — incluidas las cargas masivas por script | ✅ (esto último se agregó esta semana; antes las cargas por terminal no dejaban rastro) |
| Importación/exportación de catálogo en Excel | ✅ |
| Carga masiva de titulares desde el archivo de Conformación (botón en el panel) | ✅, agregado esta semana |
| Detección de posibles duplicados | ✅ |
| Semáforo visual de vigencia de la información | ✅ — punto verde/ámbar/rojo (90/180 días) por fila en la tabla de dependencias, con "Validado por" cuando existe |
| Validación periódica programada (recordatorio automático de "revisa esto de nuevo") | ✅ — aviso en el Dashboard (rojo si hay algo) con cuánto lleva sin actualizar tu área, más el desglose por área para admin/auditor(a) (28 ago) |
| Notificaciones automáticas al validador cuando hay cambios pendientes | ✅ — correo automático a cada validador(a) activo(a) del área cuando algo entra a revisión (28 ago); nunca bloquea el guardado si el envío falla |

### 2.3 Capa de métricas y análisis

Casi todo lo que el documento original pedía para esta capa **ya está implementado y visible** en el panel (`GET /admin/metricas/resumen`, pestaña de estadísticas):

- Total de consultas, % resueltas, % sin resultado
- Top 10 búsquedas más frecuentes y top 10 sin resultado (esto **es** el "motor de descubrimiento de necesidades" que el plan original marcaba como pendiente)
- % de consultas por voz, % con modo accesible activo, % que preguntaban por accesibilidad
- Consultas por sede, por área, por tipo de dependencia
- Completitud de datos por área (horario, teléfono, accesibilidad confirmada)
- Pendientes de aprobar por área, con antigüedad promedio en días
- Reporte descargable en Excel de todo lo anterior

Lo que sigue faltando de esta capa: una **medición de línea base** (antes de que existiera Justicia Orienta) para poder mostrar "reducción de derivaciones incorrectas" o "reducción de colas en el MAU" como comparación — eso requiere una semana de conteo manual en el MAU antes de lanzar el piloto, no una tarea de código.

---

## 3. Modelo de gobernanza y roles (heredado del original, con estado real agregado)

```
                      COMITÉ DIRECTIVO
        (Gerencia de Administración, ODANC, Presidencia)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ADMINISTRADOR     VALIDADOR       AUDITOR
        DEL SISTEMA       GENERAL         GENERAL
     (Coord. Informática) (Planeamiento)  (ODANC)
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                RESPONSABLES DE CONTENIDO
                    (uno por área, abajo)
```

Los tres roles técnicos (administrador/validador/auditor) ya existen como roles reales del sistema (`Rol.admin`, `Rol.validador`, `Rol.auditor`) — falta asignarlos formalmente a personas concretas de cada oficina.

### 3.1 Qué área nutre al sistema, y con qué registros — estado real por área

Esta es la tabla que responde directamente "qué área nutrirá al sistema y qué registros se encargará respectivamente", igual que el documento original, pero con una columna nueva: **estado real de avance hoy**.

| # | Área | Qué registra en el sistema | Datos específicos | Estado real hoy |
|---|---|---|---|---|
| **Áreas jurisdiccionales** | | | | |
| 1 | Salas Superiores | Ubicación, horario, especialidad, vocales, servicios | Sala, piso, oficina, teléfono, horario de audiencias | ⚠️ Ubicación cargada (directorio oficial); vocales cargados solo si la sala es jurisdiccional/ODECMA de la sede piloto |
| 2 | Juzgados | Ubicación, horario, especialidad, juez/a titular, servicios | Juzgado, piso, oficina, horario de atención, requisitos | ✅ Sede piloto: ubicación + titular real cargados (69 juzgados con juez/a) |
| 3 | Módulos (JPL, etc.) | Ubicación, horario, especialidad, servicios | Módulo, piso, oficina, servicios especializados | ⚠️ Solo ubicación, vía directorio general |
| **Áreas administrativas** | | | | |
| 4 | Gerencia de Administración | Ubicación, horario, servicios, procedimientos | Oficina, piso, trámites administrativos | ⚠️ Solo ubicación |
| 5 | Unidad de Servicios Judiciales | Ubicación, horario, servicios, requisitos | Oficina, piso, servicios que ofrece | ⚠️ Solo ubicación |
| 6 | Unidad de Planeamiento y Desarrollo | Ubicación, horario, proyectos, información institucional | Oficina, piso, documentos de gestión | ⚠️ Solo ubicación |
| 7 | Unidad de Administración y Finanzas | Ubicación, horario, trámites financieros | Oficina, piso, procedimientos | ⚠️ Solo ubicación |
| 8 | **Coordinación de Informática** | Ubicación, soporte técnico, servicios informáticos — **y administra el sistema completo** | Oficina, piso, canales de soporte | ✅ Único responsable técnico activo hoy; ubicación + anexo cargados |
| 9 | Recursos Humanos | Ubicación, horario, trámites de personal | Oficina, piso, procedimientos de personal | ⚠️ Solo ubicación |
| 10 | Logística y Abastecimiento | Ubicación, horario, procedimientos de compras | Oficina, piso, procesos de adquisición | ⚠️ Solo ubicación |
| 11 | Archivo Central | Ubicación, horario, servicios de archivo | Oficina, piso, procedimientos | ⚠️ Solo ubicación |
| 12 | Oficina de Imagen Institucional | Ubicación, comunicación, información institucional | Oficina, piso, materiales de comunicación | ⚠️ Solo ubicación |
| **Servicios al ciudadano** | | | | |
| 13 | Mesa de Partes (cada sede) | Ubicación, horario, recepción de documentos, requisitos | Piso, teléfono, documentos requeridos | ✅ 4 mesas de partes de la sede piloto con ubicación y anexo |
| 14 | Centro de Distribución | Ubicación, horario, distribución de expedientes | Piso, teléfono, procedimientos | ⚠️ Solo ubicación |
| 15 | Módulo de Atención al Usuario (MAU) | Ubicación, horario, orientación, servicios de apoyo | Piso, teléfono, servicios de orientación | ⚠️ Solo ubicación |
| 16 | Orientación Judicial | Ubicación, horario, orientación legal | Piso, teléfono, canales de orientación | ⚠️ Solo ubicación |
| **Sedes y servicios generales** | | | | |
| 17 | Cada sede (26 en total) | Dirección, horario, accesibilidad, estacionamiento, fotos, plano interno | Nombre, dirección, servicios, accesibilidad | ⚠️ Dirección y central telefónica cargadas para las 26; accesibilidad, fotos y plano interno: 0% |

**Lectura honesta de esta tabla:** hoy, de las 17 filas, solo la **fila 8 (Coordinación de Informática)** tiene un responsable de contenido real, activo, validando y publicando. Las otras 16 áreas tienen su ubicación cargada automáticamente desde el directorio oficial (en estado "revisión", nadie de esas áreas lo validó todavía) — el sistema está listo para que cada una tome posesión de su fila, pero eso requiere una decisión institucional (asignar responsables), no una tarea de programación.

### 3.2 Flujo de validación de contenido (heredado, sin cambios — ya implementado tal cual)

1. El responsable de área registra/edita en el panel → 2. Auditoría registra usuario+fecha+campo anterior/nuevo → 3. Notificación por correo a cada validador(a) del área → 4. El validador de esa área aprueba o rechaza → 5. Publicación → 6. Queda visible al ciudadano.

Los seis pasos ya funcionan exactamente así hoy (paso 3 agregado el 28 de agosto).

---

## 4. Arquitectura del sistema (actualizada)

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA DE EXPERIENCIA                                         │
│  Web (hoy) · App móvil (futuro) · Kiosco (futuro) · Tablet   │
├─────────────────────────────────────────────────────────────┤
│  CAPA DE SERVICIOS                                           │
│  Búsqueda inteligente (texto/voz, tolerante a errores) ·     │
│  Orientación 3 niveles (parcial) · Accesibilidad completa    │
├─────────────────────────────────────────────────────────────┤
│  CAPA DE DATOS                                                │
│  PostgreSQL persistente (Neon) · Sedes · Edificios ·          │
│  Dependencias · Servicios · Alias · Titulares · Auditoría ·   │
│  Consultas (analítica anónima)                                │
├─────────────────────────────────────────────────────────────┤
│  CAPA DE GOBERNANZA                                           │
│  Gestión de contenido por área · Auditoría · Métricas         │
└─────────────────────────────────────────────────────────────┘
```

**Costo de infraestructura hoy: $0.** FastAPI + SQLAlchemy + PostgreSQL (todo código abierto), hosting en capa gratuita de Render, base de datos en capa gratuita de Neon. Sin licencias, sin contratos, sin hardware nuevo.

---

## 5. Calendario de implementación (recalibrado a fechas reales)

El calendario original hablaba de "semanas 1 a 8" en abstracto. Esta versión usa fechas de calendario reales, alineadas a las bases del concurso (recepción de postulaciones: 18–31 de agosto de 2026 — hoy es 25 de agosto).

### Fase 0 — Ya logrado (no es una tarea futura, es el punto de partida real)

| Logro | Fecha |
|---|---|
| Piloto desplegado en producción, con base de datos persistente | Semana del 18 de agosto |
| Directorio oficial cargado: 26 sedes, 505 dependencias | 21 de agosto |
| Titulares reales cargados: 73 magistrados/jefaturas (sede piloto) | 21 de agosto |
| Botón de carga de titulares en el panel (autoservicio, sin depender de un desarrollador) | 21 de agosto |
| Auditoría completa, incluidas las cargas masivas | 21 de agosto |
| Postulación al concurso redactada, verificada contra las bases, y con evidencia visual real | 24–25 de agosto |

### Fase 1 — Lo que falta antes del cierre de postulaciones (25–31 de agosto de 2026)

| Fecha | Actividad | Responsable | Prioridad |
|---|---|---|---|
| 25–26 ago | Completar hoja de identificación (nombres, correos, firmas reales) e imprimir 5 sobres | Coord. Informática + firma del jefe/coordinador | 🔴 Crítica |
| 26–27 ago | Conseguir la firma de aprobación del responsable (coordinador de la especialidad) | Coord. Informática | 🔴 Crítica |
| 27–29 ago | Entregar la postulación (presencial en ODANC o virtual al correo indicado en las bases) | Coord. Informática | 🔴 Crítica |
| Antes del 31 ago | *(Opcional, si hay tiempo)* Cargar accesibilidad confirmada (rampa/ascensor/baño) de la sede piloto — hoy en blanco | Administración de sede | 🟡 Media |

No hay margen realista para nuevas funcionalidades de código antes del cierre — el sistema que se presenta es el que existe hoy, y ya es sólido.

### Fase 2 — Consolidación (setiembre–noviembre 2026, si se gana o de todos modos)

| Mes | Actividad | Responsable |
|---|---|---|
| Set. | Asignar un responsable real por cada una de las 16 áreas restantes de la tabla 3.1 | Comité Directivo |
| Set. | Cada área valida y publica su propia información (hoy está en "revisión") | Cada área |
| Set.–Oct. | Implementar el semáforo visual de vigencia (dato ya existe, falta la UI) | Coord. Informática |
| Oct. | Implementar notificación automática al validador cuando hay contenido pendiente | Coord. Informática |
| Oct. | Construir la "ficha de sede" completa (vista única con horario, accesibilidad, todas sus dependencias) | Coord. Informática |
| Oct.–Nov. | Cargar titulares de áreas administrativas (RRHH, Logística, Gerencia, etc.) desde sus propios registros | Cada área + Coord. Informática |
| Nov. | Medir línea base real (una semana de conteo manual en el MAU) y comparar contra el piloto | Unidad de Planeamiento |

### Fase 3 — Expansión (diciembre 2026 – agosto 2027)

| Periodo | Actividad |
|---|---|
| Dic.–Ene. | Completar accesibilidad confirmada (rampa/ascensor/baño) en las 26 sedes |
| Feb.–Mar. | Cargar horarios, requisitos y ruta interna (`instrucciones_internas`) piso por piso |
| Abr.–May. | Evaluar modo offline (PWA) si el uso móvil lo justifica |
| Jun.–Jul. | Documentar formalmente el modelo de replicación (ya probado en la práctica) para otras sedes/Cortes |
| Ago. 2027 | Revisión anual del modelo, ajuste del comité de mejora |

### Fase 4 — Innovación y replicabilidad nacional (2027–2028)

Ninguna de estas actividades existía en el sistema al 25 de agosto ni estaba en el plan original. Nacieron de la revisión estratégica de ese día (ver sección 6, "Visión Estratégica: de buscador a acompañante") y son las que convierten a Justicia Orienta de un directorio inteligente en un modelo institucional que otras cortes del país puedan adoptar. La columna "Estado" se agregó el 27 de agosto, tras dos días más de desarrollo (ver §0.1).

| # | Actividad | Responsable | Prioridad | Estado (27 ago) |
|---|---|---|---|---|
| 1 | Diseñar y prototipar la "Ruta de Atención" (servicio → dependencia → ubicación → cómo llegar → ruta accesible) | Coord. Informática + Unidad de Planeamiento | 🟡 Alta | ⚠️ Parcial — chips "¿Qué necesitas hacer?" en la portada (28 ago) adelantan el paso 1 con 3 tareas frecuentes (demanda, multa, consultar caso); "cómo llegar" y "ruta accesible" ya existen (mapa interno, ítem 2); falta que arranque de verdad desde el modelo `Servicio`, no de un término de búsqueda fijo |
| 2 | Construir Ficha de Sede completa (mapa por piso, fotografías, ascensores, botón "Estoy aquí") | Coord. Informática + Administración de sede | 🟡 Alta | ⚠️ Parcial — "Estoy aquí" ya muestra dirección/horario/teléfono/accesibilidad y sus dependencias agrupadas por piso (28 ago), con el mapa interno (Nivel 1 real + genérico pisos 4-20) para la sede piloto; falta fotografía por piso y extenderlo a las otras 25 sedes |
| 3 | Conectar el modelo de Servicio ya existente al flujo de Ruta de Atención | Coord. Informática | 🟡 Alta | ❌ Pendiente (depende del ítem 1) |
| 4 | Convertir "No sé qué necesito" en un flujo conversacional progresivo | Coord. Informática | 🟡 Alta | ⚠️ Parcial (31 ago) — selector de perfil opcional (adulto mayor/accesibilidad/dificultad visual) + detección de intención por palabras clave dentro de una búsqueda normal, sin IA generativa; elegir "Soy adulto mayor" activa además el nuevo Modo Adulto Mayor (texto e interfaz ampliados, menos elementos en pantalla); sigue siendo una tarjeta estática para "No sé qué necesito" en sí, no un flujo conversacional completo |
| 5 | Evaluar un asistente de IA institucional para trámites y procedimientos -- entrenado y acotado al catálogo validado de la Corte (nunca respuestas libres o inventadas) | Coord. Informática + Unidad de Planeamiento | 🟠 Media | ❌ Pendiente, deliberadamente — requiere una fuente de contenido validado que hoy no existe |
| 6 | Agregar botón "Necesito ayuda" con salida a orientación humana (MAU, teléfono, canales oficiales) | Coord. Informática + MAU | 🟡 Alta | ✅ Hecho — tarjeta "Necesito ayuda" en la portada pública; desde el 31 ago también permite "Solicitar que me llamen o me escriban" (código de seguimiento JO-AAAA-NNNNNN, sin cuenta ni contraseña) |
| 7 | Rediseñar los accesos rápidos del frontend: Buscar / Estoy aquí / Necesito ayuda / Accesibilidad | Coord. Informática | 🟠 Media | ✅ Hecho — portada con los 4 accesos, más el rediseño completo del panel de administración |
| 8 | Cerrar el ciclo del motor de descubrimiento: asignación automática a área responsable y seguimiento | Coord. Informática + Comité de Mejora | 🟡 Alta | ⚠️ Parcial — "Solicitudes de cobertura" ya asigna un área y hace seguimiento del estado (`app/routers/admin_cobertura.py`), pero la asignación la hace un(a) admin, no es automática |
| 9 | Definir metodología formal de medición de "primera orientación correcta" y reducción de derivaciones | Unidad de Planeamiento | 🟡 Alta | ✅ Hecho — `Metodologia_Medicion_Indicadores_JusticiaOrienta.docx`, con el mismo indicador ya visible en el dashboard del panel |
| 10 | Ampliar el semáforo de vigencia con "Validado por" y "Próxima revisión programada" | Coord. Informática | 🟠 Media | ✅ Hecho |
| 11 | Formalizar la trazabilidad de la orientación en una sola vista auditable | Coord. Informática | 🟠 Media | ✅ Hecho — botón "Trazabilidad" por dependencia en el panel |
| 12 | Redactar política formal de protección de datos (qué se guarda, qué no, base legal) | ODANC / Asesoría Legal | 🟡 Alta | ✅ Hecho — `Politica_Proteccion_Datos_JusticiaOrienta.docx` |
| 13 | Evaluar modo offline esencial (PWA: sedes, pisos, dependencias, teléfonos, horarios, emergencia) | Coord. Informática | 🟠 Media | ✅ Hecho — `app/static/sw.js` + `manifest.json`, ya en producción |
| 14 | Documentar el modelo como paquete replicable (manual + código abierto) | Unidad de Planeamiento + Presidencia | 🟡 Alta | ❌ Pendiente (institucional, no requiere código) |
| 15 | Presentar el modelo a otras cortes superiores del país (mesa de intercambio interinstitucional) | Presidencia de la Corte | 🟠 Media | ❌ Pendiente (institucional) |

---

## 6. Visión estratégica: de buscador a acompañante (Fase 4, desarrollo conceptual)

Todo lo descrito en las secciones 1 a 5 es el sistema tal como existe hoy: un directorio inteligente que responde con precisión *dónde* y *quién*. Esta sección describe el salto que lo convierte de buscador en acompañante — el elemento que distingue a un directorio digital de un modelo institucional replicable. **Ninguno de los elementos de esta sección existe todavía en el sistema**; están desarrollados como Fase 4 en la sección 5.

### 6.1 El cambio de paradigma

Hoy, ante "quiero presentar una demanda", el sistema responde "Mesa de Partes está en X". El salto es que responda: *"Para ese trámite existe este canal. Puedes hacerlo presencialmente en X o usar X si corresponde. ¿Quieres que te explique las opciones?"*

| Hoy | Propuesto (Fase 4) |
|---|---|
| Busca → encuentra | Necesita algo → se le acompaña hasta resolverlo |

### 6.2 La Ruta de Atención

El concepto central de la Fase 4: cada necesidad del ciudadano recorre cinco preguntas, no una sola búsqueda.

| Paso | Pregunta | Resultado |
|---|---|---|
| 1 | ¿Qué necesita? | Servicio identificado |
| 2 | ¿Quién lo atiende? | Dependencia responsable |
| 3 | ¿Dónde? | Sede / piso / oficina |
| 4 | ¿Cómo llegar? | Mapa externo + ruta interna |
| 5 | ¿Necesita atención accesible? | Ruta accesible alternativa |

El paso 5 ya es real dentro del mapa interno (28 ago): un tramo del grafo se marca `es_accesible` (falso solo en escaleras sin ascensor alterno, verdadero por defecto), y el ciudadano puede pedir "necesito una ruta accesible" al calcular la ruta -- Dijkstra directamente ignora esos tramos en vez de calcular la más corta y recién después avisar que no sirve. Falta lo mismo para el paso 1 (arrancar desde un servicio, no desde una dependencia ya identificada) — ver ítem 1 de la tabla de Fase 4.

El modelo `Servicio` (canal, requisitos, costo) ya existe en la base de datos, sin conectar a ningún flujo. La Fase 4 lo conecta a esta ruta.

### 6.3 La sede como lugar físico: Ficha de Sede completa

Ya existe: dirección, horario, teléfono, 5 campos de accesibilidad. Falta: pisos navegables, ascensores, mapa por piso, fotografías de referencia, directorio unificado, botón "Estoy aquí". Las fotografías de referencia (el ingreso, los ascensores, la puerta del juzgado) ayudan especialmente a adultos mayores, personas que llegan por primera vez, personas con ansiedad y personas con dificultades cognitivas.

### 6.4 El motor de descubrimiento como ciclo cerrado

Hoy el motor de descubrimiento (sección 2.3) termina en un número: el top de búsquedas sin resultado. La Fase 4 lo cierra:

Ciudadano pregunta → no encuentra (✅ ya se mide) → se registra y se agrupa (✅ ya existe) → se analiza (✅ ya existe, dashboard) → **se asigna automáticamente al área responsable (nuevo)** → **el área genera la información o el servicio faltante (nuevo)** → se publica (✅ ya existe el flujo de aprobación) → **se vuelve a medir — el ciclo se cierra con evidencia, no con intuición (nuevo)**.

### 6.5 Vigencia, trazabilidad y confianza institucional

- **Semáforo ampliado:** agregar campos "Validado por" y "Próxima revisión programada", además del cálculo automático verde/ámbar/rojo por antigüedad ya diseñado.
- **Trazabilidad de la orientación:** ante cualquier auditoría, el sistema debe poder reconstruir automáticamente por qué respondió lo que respondió — dependencia, dato publicado, quién lo validó, cuándo. Hoy esta información existe repartida en dos tablas (`Auditoria` y `ConsultaLog`); falta unirla en una sola vista.

### 6.6 Protección de datos: compromiso institucional explícito

El sistema ya no guarda DNI, nombre, expediente, ubicación permanente ni grabaciones de voz — eso ya es una buena práctica de diseño, verificada en `ConsultaLog`. Lo que falta es formalizarlo como política institucional escrita: qué se guarda, qué no, y con qué base legal, especialmente tratándose del Poder Judicial.

### 6.7 Una interfaz que acompaña, no que abruma

Cuatro accesos claros y nada más: Buscar, Estoy aquí, Necesito ayuda, Accesibilidad. El botón "Necesito ayuda" no debe sentirse como un error — debe llevar a orientación humana real: MAU, canales oficiales, teléfono, ubicación del módulo de atención.

### 6.8 Un asistente de IA, pero acotado y auditable

Preguntas como "¿cómo registro una demanda?" o "¿cómo solicito antecedentes?" no son una búsqueda de dependencia: son un trámite. Hoy el sistema responde con honestidad que no puede identificar la consulta, en vez de inventar una respuesta — eso ya es una decisión de diseño deliberada (ver `app/nlp.py`: "nunca inventar, siempre poder explicar por qué se sugirió algo"). La Fase 4 lleva esa misma filosofía un paso más allá: un asistente de IA **entrenado y acotado al catálogo validado de trámites y servicios de la Corte**, que usa lenguaje natural para *entender* la pregunta y encontrar el trámite correcto, pero que **solo responde con contenido ya aprobado por el área responsable** — nunca con una respuesta generada libremente. La IA resuelve el "entender qué pregunta la persona"; la Corte sigue siendo la única fuente de la respuesta.

**"Justi" (31 ago):** se le puso nombre a la orientación que el sistema ya da — sin avatar, sin personaje 3D, sin IA generativa (eso rompería el costo cero y el principio de "nunca inventar"). Un enlace "¿Cómo funciona Justi?" en el pie de página documenta 10 reglas reales y verificables del sistema (nunca inventa, no da asesoría legal, prioriza accesibilidad, no guarda datos personales, etc.) — comunica la misma filosofía de esta sección, en lenguaje ciudadano. También se agregó control de velocidad de voz (🐢 Voz más lenta), pedido explícito de `ProyectoJusticia22.doc`.

### 6.9 Por qué esto vuelve al proyecto replicable

La arquitectura ya demostró que 26 sedes se cargan sin cambiar una línea de código. La Fase 4 demuestra que la experiencia también escala — y es lo que convierte a Justicia Orienta de un sistema hecho a medida de una sede en un modelo que cualquier corte superior del país puede adoptar sin reinventarlo.

---

## 7. Comité de mejora (heredado, es organizacional — no requiere código)

| Rol | Quién | Frecuencia |
|---|---|---|
| Coordinador | Unidad de Planeamiento y Desarrollo | Mensual |
| Representante técnico | Coordinación de Informática | Mensual |
| Representantes de área | Responsable de contenido de cada área activa | Mensual |
| Representante del MAU | Encargado del módulo | Mensual |
| Representante de ODANC | Designado por la Jefatura | Trimestral |

**Agenda tipo:** reporte de métricas (ya generadas automáticamente por el sistema) → análisis de búsquedas sin resultado (top 10 ya calculado) → estado de actualización por área → incidencias → plan de acción con responsables y plazos.

---

## 8. Entregables — lo que ya existe vs. lo que falta

| Documento | Estado |
|---|---|
| Propuesta de concurso (2-4 páginas, formato oficial) | ✅ `Concurso_JusticiaOrienta_Propuesta.pdf` |
| Hoja de identificación | ✅ Incluida en el mismo PDF (página aparte) |
| Etiqueta para el sobre | ✅ Incluida en el mismo PDF |
| Manual del panel de administración | ✅ `JusticiaOrienta_06_Manual_Panel_Administracion.docx` |
| Manual del ciudadano | ✅ `JusticiaOrienta_07_Manual_Ciudadano.docx` |
| Plantilla de catálogo para carga masiva | ✅ `JusticiaOrienta_04_Plantilla_Catalogo_Piloto.xlsx` |
| Diseño del servicio | ✅ `JusticiaOrienta_00_Diseno_Servicio.html` |
| Modelo de datos técnico | ⚠️ Existe en el código (`app/models/`) pero no como documento aparte para no técnicos |
| Guía de replicación formal | ❌ Pendiente (la capacidad ya existe y está probada) |
| Política de protección de datos | ✅ `Politica_Proteccion_Datos_JusticiaOrienta.docx` (27 ago) |
| Metodología de medición de indicadores | ✅ `Metodologia_Medicion_Indicadores_JusticiaOrienta.docx` (27 ago) |
| Política de voz y grabación | ⚠️ El diseño ya es privado por defecto (el reconocimiento de voz lo procesa el navegador, nada se graba ni se envía a un servidor) — falta redactarlo como política formal |
| Logotipo institucional definitivo | ❌ Existe una marca abstracta simple; no se adoptó la propuesta de balanza+brújula (decisión ya tomada: se mantiene como está) |

---

## 9. Cierre

Justicia Orienta no es una idea en papel esperando construirse: es un sistema real, con datos reales de una sede real de la Corte Superior de Justicia de Lima, que ya resuelve las tres preguntas que un ciudadano se hace al llegar — *dónde, quién y cómo* — para más de 170 dependencias, con 73 magistrados y jefaturas identificados por su nombre real, sin que haya costado un sol en licencias.

Lo que falta no es tecnología: es que cada área de la Corte tome posesión de su propia fila en la tabla de gobernanza. El sistema ya está listo para recibirlas.

> *"La justicia no debe ser un laberinto. Debe ser un camino claro, accesible y comprensible para todos."*

---

**Documento generado:** 25 de agosto de 2026
**Basado en:** `ProyectoJusticia.doc` (v1.0) + verificación directa contra `E:\PROGRAMACION\JustiOrienta` (código) y producción (`justicia-orienta.onrender.com`)
**Próxima revisión sugerida:** al cierre de la Fase 1 (31 de agosto de 2026)
