# Análisis de factibilidad: ideas de `ProyectoJusticia22.doc`

**Fecha:** 28 de agosto de 2026
**Base:** 44 ideas / 7 fases del documento `ProyectoJusticia22.doc`, verificadas contra el código real de Justicia Orienta (no contra lo que suena bien en papel) y contra el stack real: FastAPI + PostgreSQL + JavaScript plano, hosting gratuito (Render + Neon), sin presupuesto, sin equipo dedicado.

**Cómo leer este documento:** cada idea del documento original quedó clasificada en un nivel. Los niveles 1 y 2 son los que de verdad conviene priorizar ahora. Los niveles 5 y 6 no son "más difíciles" — son ideas que este proyecto, tal como está autorizado hoy, **no puede** construir por su cuenta, sin importar cuánto tiempo se le dedique.

---

## Resumen: qué hacer primero

| # | Idea | Nivel | Esfuerzo | Toca |
|---|---|---|---|---|
| 1 | Selector de perfil opcional (adulto mayor / accesibilidad / acompañante) | 2 — Factible ahora | Chico | `index.html`, `public.js` |
| 2 | Detección de intención por palabras clave (reglas, no IA) | 2 — Factible ahora | Chico-medio | `app/nlp.py` |
| 3 | "Solicitar que me llamen / escriban" con código de seguimiento | 2 — Factible ahora | Medio | nuevo modelo + router, reusa patrón de `admin_cobertura.py` |
| 4 | "Modo Adulto Mayor" (botones grandes, pocas opciones) | 2 — Factible ahora | Medio-grande | `styles.css`, `public.js`, `index.html` |
| 5 | Instrumentar tiempo/pasos por consulta (para "índice de fricción") | 3 — Factible con datos nuevos | Medio | `models/consulta.py`, `crud/busqueda.py` |
| 6 | Cargar canal de trámite (virtual/presencial) por servicio | 3 — Factible con datos nuevos | Chico (dato, no código) | carga de datos por área |
| 7 | Auditoría formal WCAG 2.2 AA + pruebas con personas reales | 8 — Proceso, no código | — | organizacional |

Todo lo demás (SIJ/SINOE, carpeta judicial, IA generativa, WhatsApp, app nativa, kioscos) se explica en detalle abajo, con la razón concreta por la que no es el siguiente paso.

---

## 1. Verificación del dato que usa el documento como argumento

El documento cita: *"En junio de 2025 la PCM aprobó el Lineamiento para el diseño y desarrollo de servicios o plataformas digitales accesibles..."* y menciona un "Sello de Accesibilidad Digital".

**Verificado — es real, no inventado:**

- **Resolución de Secretaría de Gobierno y Transformación Digital N° 001-2025-PCM/SGTD** (26 jun 2025) — exige criterios WCAG 2.2 en entidades públicas.
  https://www.gob.pe/institucion/pcm/normas-legales/6905744-001-2025-pcm-sgtd
- **Sello de Accesibilidad Digital** — convocatoria abierta desde octubre 2025.
  https://hiperderecho.org/2025/10/plataformas-accesibles-en-el-peru-se-lanzo-la-convocatoria-del-sello-de-accesibilidad-digital/
- Nota oficial de prensa del anuncio:
  https://www.radionacional.gob.pe/noticias/politica/ejecutivo-aprueba-lineamiento-para-garantizar-accesibilidad-a-los-servicios-publicos-digitales

**Conclusión:** este argumento se puede usar con confianza en la presentación del concurso — Justicia Orienta ya construye en la dirección que la propia PCM exige formalmente.

---

## 2. Ya construido (el documento no lo sabía)

El documento fue escrito sin conocer el estado real del sistema en este momento. Estas ideas ya existen:

| Idea del documento | Dónde ya existe |
|---|---|
| "Panel de inteligencia" / "qué está buscando la gente" | `app/routers/admin_metricas.py` — top búsquedas, % sin resultado, por área, por sede |
| Ficha de accesibilidad por sede (rampa, ascensor, baño, estacionamiento) | `tarjetaFichaSede()` en `public.js`, agregado el 28 ago |
| Lectura por voz | `speechSynthesis`, ya en producción |
| Alto contraste / texto ampliable / tema oscuro | `public.js`, persistido en `localStorage` |
| "Encuentra mi atención" (elegir sede → ver todo) | Tile "Estoy aquí", agrupado por piso desde el 28 ago |
| Ruta accesible alternativa (evitar escaleras) | Mapa interno, agregado el 28 ago (`es_accesible` en `ConexionNodo`) |
| Chips de tarea ("Presentar una demanda", "Pagar una multa") | Portada pública, agregado el 28 ago |
| Dashboard con indicadores para la Corte | Ya existe, con % primera orientación correcta, satisfacción, modo accesible, etc. |

---

## 3. Factible ahora, a costo cero — el siguiente paso real

### 3.1 Selector de perfil opcional

**Qué es:** al entrar, ofrecer "Soy adulto mayor / Necesito accesibilidad / Tengo dificultad visual / Estoy ayudando a otra persona / Solo quiero consultar" — nunca obligatorio.

**Cómo implementarlo:** no es una funcionalidad nueva de backend — es una capa sobre lo que ya existe. Cada opción simplemente pre-activa las preferencias de accesibilidad que ya viven en `localStorage` (alto contraste, texto grande, lectura por voz automática de resultados). "Estoy ayudando a otra persona" no necesita nada especial: es informativo, no cambia el flujo.

**Esfuerzo:** chico. Un bloque nuevo en `index.html` + un puñado de líneas en `public.js` que ya sabe activar/desactivar cada preferencia (los botones de accesibilidad ya existen, esto solo los agrupa detrás de una pregunta más humana).

### 3.2 Detección de intención por palabras clave (sin IA de pago)

**Qué es:** si alguien escribe "tiene que ir en silla de ruedas" o "mi mamá es adulta mayor", el sistema resalta directamente la información de accesibilidad de la dependencia encontrada, en vez de esperar a que la persona pregunte por separado.

**Importante — esto NO es lo que pide el punto 32 del documento** (una IA que "entiende intención" y "traduce lenguaje jurídico"). Esto es una extensión honesta de lo que `app/nlp.py` ya hace hoy: la función `es_pregunta_de_accesibilidad()` ya detecta con reglas simples si una consulta es sobre accesibilidad. Se trata de sumar un diccionario de señales ("silla de ruedas" → motora, "no veo bien" / "ciego" → visual, "adulto mayor" / "tercera edad" → perfil senior) que, al detectarse junto con una búsqueda normal, antepone la ficha de accesibilidad de la sede antes que los resultados.

**Por qué es honesto:** nunca inventa una respuesta — solo prioriza información que ya es 100% real y ya está en la base de datos. Cero costo, cero riesgo de "alucinación".

**Esfuerzo:** chico-medio. Vive enteramente en `app/nlp.py` y en cómo `public.js` ordena lo que muestra primero.

### 3.3 "Solicitar que me llamen o me escriban"

**Qué es:** un formulario simple (nombre de contacto, teléfono u correo, motivo breve) que genera un código de seguimiento (`JO-2026-000145` estilo) y aparece en el panel para que alguien del área correspondiente lo atienda.

**Cómo implementarlo:** reusa exactamente el patrón que ya existe en `app/routers/admin_cobertura.py` y `models/solicitud_cobertura.py` (que hoy asigna búsquedas sin resultado a un área con seguimiento de estado: Recibida → Derivada → En atención → Respondida). Este pedido es prácticamente el mismo modelo, con un origen distinto (un formulario directo del ciudadano, no una búsqueda fallida).

**Lo que esto NO incluye** (y no hace falta para que valga la pena): chat en vivo ni videollamada real — eso requiere personal disponible en tiempo real, que es un compromiso operativo, no de código. Esta versión es "dejo mi pedido, alguien me contacta después" — ya es un salto real de "buscador" a "atención", que es exactamente lo que pide el punto 3 del documento, sin la infraestructura de un canal en vivo.

**Esfuerzo:** medio. Un modelo nuevo (o extender `SolicitudCobertura`), un router público para crear el pedido + consultarlo por código, una vista en el panel.

### 3.4 "Modo Adulto Mayor"

**Qué es:** letra grande, botones enormes, máximo 4-5 opciones visibles, instrucciones numeradas, confirmación antes de acciones.

**Cómo implementarlo:** es una variante visual, no una reescritura. El sistema ya tiene "A+ Aumentar texto" — este modo lo llevaría más lejos (una clase CSS `.modo-mayor` en `<body>` que reduce la cantidad de elementos visibles y aumenta drásticamente tamaños), reusando componentes que ya existen en vez de crear una segunda interfaz paralela.

**Esfuerzo:** medio-grande, porque toca CSS en varias pantallas, no una sola. Vale la pena, pero no es de una tarde.

---

## 4. Factible, pero necesita datos nuevos, no solo código

### 4.1 "¿Necesitas desplazarte?" (virtual vs. presencial)

El modelo `Servicio` ya tiene un campo para el canal del trámite. La limitación hoy no es técnica: es que ningún área ha cargado todavía esa información real para sus trámites. Esto es trabajo de carga de datos por cada área, no una funcionalidad que falte programar.

### 4.2 Índice de fricción ciudadana / tiempo de orientación

Idea genuinamente buena del documento (puntos 39-41), pero hoy `ConsultaLog` no mide cuántos pasos o cuánto tiempo le toma a alguien resolver su necesidad — solo si encontró resultado o no. Para construir este indicador de verdad (no solo ponerle un nombre bonito a algo que ya existe) hace falta instrumentar sesión y tiempo, lo cual es una funcionalidad nueva con esfuerzo real, no una tarde de trabajo.

---

## 5. Requiere autorización institucional que este proyecto no tiene — no es un tema de código

Estas dos ideas no son "más difíciles de programar". Son ideas que **no pueden construirse sin que alguien con autoridad institucional lo decida primero**, sin importar cuánto esfuerzo de desarrollo se le dedique:

### 5.1 Integración con SIJ y SINOE (punto 37)

SIJ (Sistema Integrado Judicial) y SINOE (Sistema de Notificaciones Electrónicas) son sistemas judiciales reales, con datos sensibles de expedientes y notificaciones oficiales. Un piloto administrado por la Coordinación de Informática de una sola sede no tiene, y no puede autogestionarse, acceso a esos sistemas. Eso requeriría:

- Autorización a nivel de Presidencia de Corte o Gerencia de Informática nacional del Poder Judicial.
- Revisión legal y de seguridad de la información (son datos de expedientes judiciales reales).
- Muy probablemente, un convenio o resolución administrativa formal.

**Qué hacer mientras tanto:** nada de código. Si de verdad quieren avanzar esto, el siguiente paso es una conversación institucional, no una tarea de programación.

### 5.2 "Carpeta Judicial Ciudadana" (mis expedientes, mis audiencias, mis notificaciones)

Mismo bloqueo que el punto anterior, más el problema de verificar identidad real (DNI/RENIEC) para mostrar datos de un expediente a la persona correcta. El propio documento reconoce que no debería implementarse completa de inmediato — de acuerdo con eso. La recomendación aquí es más estricta todavía: ni siquiera vale la pena diseñar la arquitectura para esto ahora, porque depende por completo de una decisión institucional que todavía no existe.

---

## 6. Contradice una decisión de diseño que ya tomaron a propósito

### 6.1 IA que "entiende intención", "traduce lenguaje jurídico", "resume" (punto 32)

`app/nlp.py` documenta explícitamente, en el propio código, la decisión de **nunca inventar una respuesta, siempre poder explicar por qué se sugirió algo**. Una IA generativa real (LLM) que "traduce lenguaje jurídico a lenguaje ciudadano" no puede cumplir esa garantía sin supervisión humana constante — y además:

- Cuesta dinero (rompe el "costo cero" que sostiene todo el proyecto hoy).
- En un contexto judicial, "traducir" mal una instrucción legal tiene consecuencias reales para alguien vulnerable.

**Si en algún momento quieren esto**, es un cambio consciente de filosofía del proyecto, con presupuesto y supervisión legal — no es "el siguiente paso natural" del roadmap. La detección de intención por palabras clave (sección 3.2 de este documento) logra buena parte del mismo beneficio sin ese riesgo ni ese costo.

---

## 7. Fuera de alcance por costo o infraestructura — no ahora

| Idea | Por qué no es "gratis y ya" |
|---|---|
| WhatsApp (punto 25) | Meta Cloud API tiene capa gratuita, pero exige verificación de negocio, número dedicado, y un servidor de webhook corriendo permanentemente — un compromiso operativo nuevo, no una integración de una tarde. |
| App móvil nativa (Android/iPhone) | El sitio ya es una PWA instalable con soporte offline — cubre casi todo el beneficio real sin pagar cuota de Apple Developer ($99/año) ni mantener dos apps de tienda separadas. |
| Kioscos físicos (punto 26) | Hardware + instalación real. El propio documento ya lo marca como "fase futura espectacular" — de acuerdo, no antes. |

---

## 8. Es proceso institucional, no código

- **Auditoría formal WCAG 2.2 AA** — necesaria para el Sello de Accesibilidad Digital verificado en la sección 1. No es algo que yo pueda "programar": es una revisión (idealmente con herramientas + revisión humana) de cada pantalla contra el estándar completo.
- **Pruebas con personas con discapacidad real, co-diseño** — exactamente lo que pide el Sello de Accesibilidad Digital de la PCM. Alto valor estratégico para el concurso, pero es trabajo organizacional (reclutar participantes, coordinar sesiones), no una tarea de desarrollo.

---

## 9. Sobre el documento mismo

El punto 44 del documento recomienda "primero hacer una auditoría integral, después construir un documento maestro JUSTICIA ORIENTA 2.0". Ya existe exactamente eso: `PROYECTO_MAESTRO_JUSTICIA_ORIENTA.md`, que a diferencia de este documento nuevo, se mantiene verificado contra el código real cada vez que algo cambia (no contra lo que "debería" existir). No hace falta escribir un segundo documento maestro desde cero — lo que sí vale la pena es ir sumando las ideas de las secciones 3 y 4 de este análisis como filas nuevas ahí, a medida que se construyen.

---

## 10. Orden sugerido si se decide avanzar

1. Selector de perfil opcional (3.1) — el más chico, habilita visualmente el resto.
2. "Solicitar que me llamen o me escriban" (3.3) — el de mayor impacto narrativo para el concurso ("de buscador a atención"), reusa código ya probado.
3. Detección de intención por palabras clave (3.2) — refuerza la accesibilidad sin tocar la filosofía "nunca inventar".
4. "Modo Adulto Mayor" (3.4) — el de mayor esfuerzo de este grupo, pero el de mayor impacto humano directo.
5. Recién después: instrumentación para el índice de fricción (4.2) y carga de datos de canal por servicio (4.1).

Todo lo de las secciones 5, 6 y 7 queda fuera de este roadmap hasta que cambien las condiciones que hoy lo bloquean (autorización institucional, presupuesto, o una decisión consciente de cambiar la filosofía del proyecto).

---

## Addendum (31 ago 2026): "Justi", el orientador virtual (`robot.txt`)

Documento adicional recibido, mismo estilo/fuente que `ProyectoJusticia22.doc`, proponiendo un avatar/personaje llamado **Justi**: interfaz conversacional, avatar animado con sincronización labial, personaje 3D institucional, modos de voz ajustables, "Justi Adulto Mayor".

**Lo que ya existe, solo con otro nombre (nivel 2 — factible ahora, costo cero):**
- Los "10 principios de Justi" (nunca inventa, dice cuando no sabe, deriva a atención humana, nunca deja al ciudadano sin saber el siguiente paso) ya están implementados como filosofía de diseño en `app/nlp.py`. No hay que construir nada nuevo — hay que **nombrarlo y comunicarlo**: darle identidad ("Justi te ayuda") a la orientación que el sistema ya da, y publicar una página corta "Cómo funciona Justi" con esas reglas como compromiso documentado. Buen valor narrativo para el concurso, cero costo.
- Control de velocidad de lectura por voz — la Web Speech API (`speechSynthesis`) ya soporta `rate` de forma nativa y gratuita; hoy no está expuesto como opción para el usuario.

**Lo que contradice la decisión de diseño ya tomada (nivel 6, ver sección 6 arriba):** una IA conversacional real que "escucha → interpreta → responde por voz" sobre "tu audiencia" o "tu expediente" es generativa de verdad (cuesta dinero, y en este contexto necesitaría datos de casos que dependen de SIJ/SINOE — nivel 5, bloqueado por autorización institucional que este proyecto no tiene).

**Lo que exige presupuesto/producción real, sin aportar función (nivel 7 — fuera de alcance):** avatar 3D animado con sincronización labial es un producto de diseño/animación, no una tarea de desarrollo — 100% cosmético, no resuelve nada que el sistema no resuelva ya.

**Riesgo a vigilar:** el propio `ProyectoJusticia22.doc` advertía contra "hacer de todo junto... terminar siendo una demostración tecnológica sin impacto" (su punto 28). Un personaje 3D institucional es esa misma tentación llevada al extremo — para un piloto evaluado por impacto real, puede restar en vez de sumar. Si se retoma esta idea en la v2.0, empezar únicamente por la identidad/nombre y las reglas ya existentes, no por el avatar.
