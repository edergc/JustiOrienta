# Mi análisis y recomendación final — Justicia Orienta

**Fecha:** 31 de agosto de 2026
**Contexto:** consolida mi opinión sobre `ProyectoJusticia22.doc`, `robot.txt` ("Justi"), y mis propios hallazgos trabajando directamente en el código real durante esta sesión. Es la respuesta a "¿qué cambiarías, modificarías, implementarías, optimizarías?" — no solo qué es viable, sino qué haría yo si el proyecto fuera mío.

---

## Veredicto en una frase

Justicia Orienta ya resuelve el problema real (encontrar, llegar, ser atendido) con calidad de producción y costo cero — lo que más lo mejoraría **no** es ninguna de las ideas grandes de los dos documentos recibidos, sino cerrar la brecha de gobernanza de datos que ya existe hoy, y pulir un puñado de detalles técnicos concretos que encontré mientras trabajaba en el código.

---

## 1. Sobre los dos documentos recibidos (resumen)

El análisis completo, idea por idea, ya está en `Analisis_Factibilidad_JusticiaOrienta2.0.md` (28-31 ago). Resumen de mi postura:

- **`ProyectoJusticia22.doc`** trae ~6 ideas realmente aprovechables a costo cero (selector de perfil, detección de intención por palabras clave, "solicitar que me llamen", modo adulto mayor, entre otras) y confirmé que su argumento central (norma PCM de accesibilidad digital, junio 2025) es real, no inventado. El resto —integración con SIJ/SINOE, carpeta judicial ciudadana, IA generativa, WhatsApp, app nativa, kioscos— requiere autorización institucional, presupuesto, o contradice una decisión de diseño que el propio proyecto ya tomó a propósito.
- **`robot.txt` ("Justi")** — el avatar/personaje 3D es 100% cosmético y caro; los "10 principios de Justi" ya están implementados como filosofía en `app/nlp.py`, solo les falta nombre e identidad visible. Ponerle cara a algo que ya existe es barato; construir un personaje 3D animado no lo es y no cambia nada funcional.

No repito el detalle acá — está en el otro archivo. Lo que sigue es lo que **yo** agregaría, que ninguno de los dos documentos mencionó porque ninguno de los dos trabajó dentro del código real.

---

## 2. Lo que yo agregaría — hallazgos trabajando en el código real

### 2.1 La brecha de gobernanza ya no es una hipótesis — la medí

`PROYECTO_MAESTRO_JUSTICIA_ORIENTA.md` ya documenta que, de 17 áreas, solo Coordinación de Informática tiene un(a) responsable de contenido activo. Verifiqué qué tan concreto es esto en la base de datos real: en el indicador "Pendientes por área" del dashboard, **las 25 filas que no son la sede piloto tienen el campo `area` literalmente igual al nombre de la sede** ("Sede Miroquesada", "Sede Anselmo Barreto", "Sede Iquitos"...), no una área organizacional real ("Recursos Humanos", "Mesa de Partes", etc.).

**Por qué importa más que cualquier idea de los dos documentos:** todas las funcionalidades nuevas que se construyan (chips de tarea, avatar, ruta accesible, lo que sea) se apoyan sobre datos reales cargados por área. Si el 96% de las sedes no tiene ni siquiera el campo `area` bien puesto, ninguna funcionalidad nueva compensa eso — el "Panel de inteligencia" y el dashboard de vigencia terminan mostrando nombres de sede donde deberían mostrar áreas reales, y nadie recibe la notificación de validador (la que construimos el 27 ago) porque no hay ningún `Usuario` con `rol=validador` y `area="Sede Miroquesada"`.

**Lo que yo haría:** antes de cualquier funcionalidad nueva, una tarea de datos (no de código): para la sede piloto, decidir con la Corte 3-5 áreas reales prioritarias fuera de Coordinación de Informática (ej. Recursos Humanos, Mesa de Partes, un juzgado) y conseguir que alguien real las valide. Es la única forma de que el sistema deje de ser una demo y empiece a mostrar resultados de gobernanza real ante un jurado.

### 2.2 El "cache-busting" manual (`?v=N`) me generó bugs reales, varias veces, esta sesión

Cada vez que edité `public.js` o `admin.js`, tuve que acordarme de subir a mano el número de versión en `index.html`/`admin.html` (`?v=5` → `?v=6`...). Me olvidé de hacerlo a tiempo más de una vez esta sesión, y el síntoma fue confuso: el navegador servía JS viejo, la funcionalidad nueva "no aparecía", y tuve que diagnosticar con DevTools antes de darme cuenta de que era caché, no un bug real.

**Lo que yo cambiaría:** en vez de un número que hay que recordar subir a mano, derivar la versión automáticamente (ej. un hash corto del contenido del archivo, calculado una vez al iniciar la app, o el timestamp de build) e inyectarlo en las plantillas. Elimina una categoría entera de "bug fantasma" que ya me costó tiempo de diagnóstico dos veces distintas en esta sesión.

### 2.3 El cold start de Render (free tier) es fricción real para el ciudadano, no solo para mí

Trabajando en el sistema, choqué varias veces con el arranque en frío del plan gratuito de Render (30-90 segundos de espera antes de que cargue cualquier cosa). Eso no le pasa solo a un agente probando el sistema — le pasa a cualquier ciudadano que entra al sitio después de un rato sin visitas, justo la población que este proyecto más quiere ayudar (adultos mayores, gente que ya está ansiosa por un trámite).

**Lo que yo optimizaría, a costo cero:** un ping periódico gratuito (ej. un monitor gratuito tipo UptimeRobot, o un GitHub Actions programado cada 10-14 minutos en horario de atención) que mantenga el servicio despierto durante horas de oficina. No es una funcionalidad — es una configuración de un rato, y probablemente el cambio con mejor relación impacto/esfuerzo de todo este documento.

### 2.4 (Corregido, 31 ago) — no era un bug real

Había anotado acá 12 supuestas etiquetas `<label>` mal cerradas en `admin.html`. Al re-verificar con una búsqueda de texto literal (no un patrón de `grep` con una barra invertida mal escapada, que fue mi error original) confirmé que **las 12 están correctamente cerradas** — falsa alarma mía. Queda esta nota para que el registro sea honesto: el hallazgo original de esta sección no era real, no se hizo ningún cambio por esto.

### 2.5 Cero pruebas automatizadas de frontend

Las 143 pruebas del proyecto son todas de backend (`pytest`, endpoints, lógica de negocio) — sólidas. Pero `public.js` y `admin.js` ya suman miles de líneas y toda la verificación de esta sesión fue manual, navegador por navegador. Esto no es grave hoy (el equipo es chico, cada cambio se probó a mano), pero si el proyecto crece hacia la v2.0 con más funcionalidades de UI, la falta de cualquier red de seguridad automatizada en el frontend empieza a pesar.

**Lo que yo consideraría, sin urgencia:** no un framework de testing pesado — unas pocas pruebas de humo con algo liviano (ej. Playwright headless corriendo 3-4 flujos críticos: buscar, ver ruta, aprobar contenido) antes de que la base de código de JS vuelva a duplicarse de tamaño.

---

## 3. Mi recomendación final, todo junto, un solo orden

Combinando lo de los dos documentos externos con lo que encontré yo, este es el orden que yo seguiría cuando retomen después del concurso:

| # | Acción | Origen | Esfuerzo | Por qué primero/después |
|---|---|---|---|---|
| 1 | Ping periódico gratuito contra el cold start de Render | Hallazgo propio | Minutos-horas | Mejor relación impacto/esfuerzo de toda la lista — afecta a cada ciudadano real |
| 2 | Cache-busting automático (hash/timestamp, no `?v=N` a mano) | Hallazgo propio | Chico | Elimina una fuente de bugs que ya costó tiempo de diagnóstico dos veces |
| 3 | Decidir 3-5 áreas reales para la sede piloto y conseguir validador(es) reales | Hallazgo propio + `PROYECTO_MAESTRO` §3.1 | Institucional, no código | Sin esto, cualquier funcionalidad nueva sigue mostrando "Sede X" donde debería mostrar un área real |
| 4 | Selector de perfil opcional + detección de intención por palabras clave | `ProyectoJusticia22.doc` | Chico-medio | Barato, refuerza accesibilidad, no rompe la filosofía "nunca inventar" |
| 5 | "Solicitar que me llamen/escriban" con código de seguimiento | `ProyectoJusticia22.doc` | Medio | Reusa el patrón ya probado de `admin_cobertura.py`, salto narrativo fuerte para el concurso |
| 6 | Identidad "Justi" (nombre + página "cómo funciona") sobre lo que ya existe | `robot.txt` | Chico | Barato, buen relato, sin avatar ni IA nueva |
| 7 | "Modo Adulto Mayor" (UI grande, pocas opciones) | `ProyectoJusticia22.doc` | Medio-grande | Impacto humano alto, pero toca más pantallas — dejarlo para cuando haya más tiempo |
| 8 | Pruebas de humo de frontend (Playwright, 3-4 flujos) | Hallazgo propio | Medio | Sin urgencia, pero antes de que la v2.0 duplique el tamaño de `public.js`/`admin.js` |

Todo lo demás de ambos documentos (SIJ/SINOE, carpeta judicial, IA generativa real, avatar 3D, WhatsApp, app nativa, kioscos) queda explícitamente fuera de este orden — no porque sea mala idea, sino porque depende de autorización institucional, presupuesto, o un cambio consciente de filosofía que nadie ha decidido todavía.

---

## 4. Qué NO haría, ni en la v2.0

- No construiría el avatar 3D de "Justi" antes de tener el nombre e identidad simple funcionando y evaluada.
- No tocaría IA generativa (LLM pagado) mientras el proyecto siga financiándose a costo cero — es una decisión de presupuesto y de riesgo legal, no una mejora incremental.
- No intentaría ninguna integración con SIJ/SINOE ni "Carpeta Judicial Ciudadana" sin una autorización institucional formal por escrito — no es una cuestión de esfuerzo de desarrollo, es una puerta que este proyecto no puede abrir por su cuenta.
- No agregaría más canales (WhatsApp, app nativa) antes de resolver el punto 2.1 (gobernanza de áreas) — más canales sin datos gobernados solo multiplica el mismo problema por más superficies.

---

**En una línea para cerrar:** el sistema que tienen hoy es más sólido que cualquiera de las dos propuestas externas que recibieron — lo que más lo mejora no es una idea nueva y grande, es terminar de gobernar los datos que ya tiene, y pulir los detalles chicos que encontré con las manos en el código.
