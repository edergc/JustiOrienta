const API = "/api/v1";

// Modo offline esencial: deja disponible la app y lo ultimo ya visto
// (sedes, dependencias de una sede) sin conexion. No requiere backend
// nuevo ni cambia el buscador en linea -- ver app/static/sw.js.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // Sin service worker el sitio sigue funcionando igual con conexion,
      // solo pierde el respaldo offline -- no es un error que deba
      // interrumpir nada.
    });
  });
}

const EJEMPLOS = [
  "1 juzgado constitucional",
  "recursos humanos",
  "informatica",
  "mesa de partes",
];

const chipsBox = document.getElementById("chips");
EJEMPLOS.forEach((ej) => {
  const b = document.createElement("button");
  b.type = "button";
  b.textContent = ej;
  b.addEventListener("click", () => {
    document.getElementById("buscar").value = ej;
    actualizarBotonLimpiar();
    buscarYRenderizar(ej);
    document.getElementById("buscar").focus();
  });
  chipsBox.appendChild(b);
});

document.querySelectorAll(".tile-btn[data-ej]").forEach((b) => {
  b.addEventListener("click", () => {
    document.getElementById("buscar").value = b.dataset.ej;
    actualizarBotonLimpiar();
    buscarYRenderizar(b.dataset.ej);
    document.getElementById("buscar").focus();
  });
});

function badgeLabel(tipo) {
  return { jurisdiccional: "Jurisdiccional", administrativa: "Administrativa", servicio: "Servicio" }[tipo] || tipo;
}

function leerTexto(texto) {
  if (!("speechSynthesis" in window)) {
    alert("La lectura en voz alta no está disponible en este navegador.");
    return;
  }
  const u = new SpeechSynthesisUtterance(texto);
  u.lang = "es-PE";
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

function leerEnVozAlta(dep) {
  const enOtraSede = sedeContextoId && dep.sede && dep.sede.id !== sedeContextoId;
  const partes = [
    `${dep.nombre}.`,
    dep.titular ? `A cargo de ${dep.titular}.` : "",
    dep.sede ? `Se encuentra en ${dep.sede.nombre}` : "",
    dep.piso ? `, piso ${dep.piso}` : "",
    dep.oficina && dep.oficina !== "—" ? `, oficina ${dep.oficina}.` : ".",
    dep.telefono ? `Teléfono o anexo: ${dep.telefono}.` : "",
    enOtraSede ? `Ojo: esto está en otra sede distinta a donde te encuentras ahora.` : "",
    enOtraSede && dep.sede.direccion ? `Dirección: ${dep.sede.direccion}.` : "",
    dep.horario ? `Horario: ${dep.horario}.` : "",
    dep.ruta_accesible ? "Cuenta con ruta accesible." : "",
    dep.instrucciones_internas ? `Cómo llegar dentro del edificio: ${dep.instrucciones_internas}` : "",
  ];
  leerTexto(partes.join(" "));
}

function tarjeta(dep) {
  const el = document.createElement("article");
  el.className = "card";
  const nombreSede = dep.sede ? dep.sede.nombre : null;
  const direccion = (dep.sede && dep.sede.direccion) || [nombreSede, "Cercado de Lima"].filter(Boolean).join(", ");
  const osmQuery = encodeURIComponent(direccion || nombreSede || dep.nombre);
  const enOtraSede = Boolean(sedeContextoId && dep.sede && dep.sede.id !== sedeContextoId);

  const servicios = (dep.servicios_detalle || [])
    .map((s) => `<li><strong>${s.nombre}</strong>${s.requisitos ? " — " + s.requisitos : ""}</li>`)
    .join("");

  el.innerHTML = `
    <div class="card-top">
      <h2>${dep.nombre}</h2>
      <span class="badge ${dep.tipo}">${badgeLabel(dep.tipo)}</span>
    </div>
    <p class="meta"><strong>${nombreSede || "Sede no registrada"}</strong>${dep.piso ? " — Piso " + dep.piso : ""}${dep.oficina ? ", oficina " + dep.oficina : ""}</p>
    ${dep.titular ? `<p class="meta"><strong>A cargo:</strong> ${dep.titular}</p>` : ""}
    ${dep.telefono ? `<p class="meta"><strong>Teléfono / anexo:</strong> ${dep.telefono}</p>` : ""}
    ${enOtraSede ? `
      <div class="otra-sede">
        Esto está en otra sede, no en la que estás ahora.
        <span>${nombreSede}${direccion ? " — " + direccion : ""}</span>
      </div>` : ""}
    ${dep.horario ? `<p class="meta">Horario: ${dep.horario}</p>` : ""}
    ${dep.servicios ? `<p class="meta">${dep.servicios}</p>` : ""}
    ${servicios ? `<ul class="meta" style="padding-left:1.1rem; margin-top:0.4rem;">${servicios}</ul>` : ""}
    ${dep.instrucciones_internas ? `<p class="meta"><strong>Cómo llegar dentro del edificio:</strong> ${dep.instrucciones_internas}</p>` : ""}
    <div class="a11y-row">
      ${dep.rampa || (dep.sede && dep.sede.rampa) ? "<span>Rampa</span>" : ""}
      ${dep.ascensor || (dep.sede && dep.sede.ascensor) ? "<span>Ascensor</span>" : ""}
      ${dep.banio_accesible || (dep.sede && dep.sede.banio_accesible) ? "<span>Baño accesible</span>" : ""}
    </div>
    <div class="card-actions">
      <button class="primary" type="button" data-leer>🔊 Escuchar</button>
      ${!enOtraSede && dep.sede ? `<button type="button" data-ruta-interna>🧭 ¿Cómo llego desde aquí?</button>` : ""}
      <a href="https://www.openstreetmap.org/search?query=${osmQuery}" target="_blank" rel="noopener">${enOtraSede ? "Cómo llegar hasta esa sede" : "Cómo llegar"} (OpenStreetMap)</a>
    </div>
    <div class="ruta-interna-panel" style="display:none;"></div>
  `;
  el.querySelector("[data-leer]").addEventListener("click", () => leerEnVozAlta(dep));
  const btnRuta = el.querySelector("[data-ruta-interna]");
  if (btnRuta) btnRuta.addEventListener("click", () => alternarRutaInterna(el, dep));
  return el;
}

// Wayfinding auto-declarado dentro de un edificio (Fase 4, "mapa interno"):
// el ciudadano elige en cuál de los puntos reconocibles de la sede está
// parado, y el sistema arma la ruta paso a paso hasta la dependencia. Se
// consulta bajo demanda (recién al hacer clic), no en cada tarjeta, para no
// pedir datos que la mayoría de resultados todavía no tiene cargados.
async function alternarRutaInterna(tarjetaEl, dep) {
  const panel = tarjetaEl.querySelector(".ruta-interna-panel");
  if (panel.style.display !== "none") {
    panel.style.display = "none";
    return;
  }
  panel.style.display = "block";
  panel.innerHTML = `<p class="hint">Cargando…</p>`;
  try {
    const puntos = await (await fetch(`${API}/sedes/${dep.sede.id}/puntos-partida`)).json();
    if (!puntos.length) {
      panel.innerHTML = `<p class="hint">Todavía no hay una ruta interna cargada para esta sede.</p>`;
      return;
    }
    panel.innerHTML = `
      <label style="font-weight:700; font-size:0.9rem;">¿Dónde estás ahora?</label>
      <div class="search-row" style="margin-top:0.4rem;">
        <select>${puntos.map((p) => `<option value="${p.id}">${p.nombre}${p.piso ? " (piso " + p.piso + ")" : ""}</option>`).join("")}</select>
        <button type="button" class="go">Ver ruta</button>
      </div>
      <div class="ruta-resultado"></div>
    `;
    panel.querySelector("button.go").addEventListener("click", () => calcularYMostrarRuta(panel, dep));
  } catch {
    panel.innerHTML = `<p class="hint">No pudimos cargar los puntos de referencia. Intenta de nuevo.</p>`;
  }
}

// ── Mapa visual del Nivel 1 (Sede Javier Alzamora Valdez) ──
// Diagrama esquemático propio (formas dibujadas a mano, no una copia de
// ningún plano de terceros) que respeta la disposición real documentada:
// planta en forma de abanico curvo, auditorio al fondo, dos bloques (A hacia
// Av. Abancay, B hacia Av. Nicolás de Piérola) y la plaza semicircular al
// frente. Las posiciones de cada punto (pos_x/pos_y, 0-100) se cargaron a
// mano comparando el plano real -- ver app/cargar_mapa_jav_nivel1.py.
const MAPA_FONDO_SVG = `
  <path class="mapa-edificio" d="M12,55 C8,35 20,15 42,10 C55,6 70,8 80,14
    C92,18 95,30 90,42 C88,55 85,62 78,68 C74,76 68,84 58,90
    C50,95 50,95 42,90 C32,84 26,76 22,68 C15,62 12,58 12,55 Z" />
  <path class="mapa-plaza" d="M30,90 C36,98 64,98 70,90 L70,100 L30,100 Z" />
  <text class="mapa-rotulo" x="6" y="45" transform="rotate(-70 6 45)">Av. Nicolás de Piérola</text>
  <text class="mapa-rotulo" x="94" y="45" transform="rotate(70 94 45)">Av. Abancay</text>
  <text class="mapa-rotulo" x="72" y="9" transform="rotate(28 72 9)">Jr. Apurímac</text>
  <text class="mapa-rotulo" x="50" y="99" text-anchor="middle">Plaza</text>
`;

function renderMapaSVG(pasos) {
  const ultimo = pasos.length - 1;
  const linea = pasos.map((p) => `${p.pos_x},${p.pos_y}`).join(" ");
  const pines = pasos
    .map((p, i) => {
      const esOrigen = i === 0;
      const esDestino = i === ultimo;
      const clase = esOrigen ? "origen" : esDestino ? "destino" : "punto";
      const r = esOrigen || esDestino ? 2.6 : 1.5;
      const etiqueta =
        esOrigen ? "Estás aquí" : esDestino ? escaparHtmlPublico(p.nombre) : null;
      const texto = etiqueta
        ? `<text class="mapa-pin-etiqueta ${esDestino ? "destino" : ""}" x="${p.pos_x}" y="${p.pos_y - r - 1.6}" text-anchor="middle">${etiqueta}</text>`
        : "";
      return `<g><title>${escaparHtmlPublico(p.nombre)}</title><circle class="mapa-pin ${clase}" cx="${p.pos_x}" cy="${p.pos_y}" r="${r}" />${texto}</g>`;
    })
    .join("");
  return `
    <div class="mapa-ruta-contenedor">
      <svg class="mapa-ruta-svg" viewBox="0 0 100 100" role="img" aria-label="Mapa del Nivel 1 con la ruta resaltada" preserveAspectRatio="xMidYMid meet">
        ${MAPA_FONDO_SVG}
        <polyline class="mapa-ruta-linea" points="${linea}" />
        ${pines}
      </svg>
    </div>
  `;
}

// ── Diagrama genérico "planta típica" (pisos 4 al 20) ──
// No hay datos de qué oficina exacta ocupa cada piso, así que este esquema
// no representa un piso real en particular -- solo el patrón que sí está
// documentado y se repite en esos pisos (hall de ascensores central rodeado
// por un anillo de oficinas, con una sala de reuniones en cada extremo).
// Sirve para que el ciudadano ubique el tipo de piso al que llega, no la
// puerta exacta -- mismo espíritu que el aviso de texto que reemplaza.
const PISO_TIPICO_MIN = 4;
const PISO_TIPICO_MAX = 20;

const OFICINAS_TIPICAS = [
  [16, 34], [13, 44], [14, 54], [19, 63],
  [84, 34], [87, 44], [86, 54], [81, 63],
];
const SALAS_REUNION_TIPICAS = [[27, 71], [73, 71]];

function renderMapaGenericoSVG(piso, nombreDestino) {
  const oficinas = OFICINAS_TIPICAS.map(([x, y]) => `<circle class="mapa-oficina-tipica" cx="${x}" cy="${y}" r="2.2" />`).join("");
  const salas = SALAS_REUNION_TIPICAS
    .map(([x, y]) => `<g><title>Sala de reuniones</title><circle class="mapa-sala-tipica" cx="${x}" cy="${y}" r="3" /></g>`)
    .join("");
  return `
    <div class="mapa-ruta-contenedor">
      <svg class="mapa-ruta-svg" viewBox="0 0 100 92" role="img" aria-label="Esquema típico del piso ${escaparHtmlPublico(piso)}" preserveAspectRatio="xMidYMid meet">
        <ellipse class="mapa-edificio" cx="50" cy="48" rx="44" ry="40" />
        ${oficinas}
        ${salas}
        <g><title>Hall de ascensores -- llegaste aquí</title><circle class="mapa-pin origen" cx="50" cy="22" r="3.2" /></g>
        <text class="mapa-pin-etiqueta" x="50" y="15" text-anchor="middle">Hall de ascensores</text>
        <text class="mapa-rotulo-piso" x="50" y="86" text-anchor="middle">Piso ${escaparHtmlPublico(piso)} -- distribución típica</text>
      </svg>
      <p class="hint mapa-tipica-aviso">Pregunta en este piso por "${escaparHtmlPublico(nombreDestino)}".</p>
    </div>
  `;
}

async function calcularYMostrarRuta(panel, dep) {
  const origenId = panel.querySelector("select").value;
  const resultado = panel.querySelector(".ruta-resultado");
  resultado.innerHTML = `<p class="hint">Calculando ruta…</p>`;
  try {
    const res = await fetch(`${API}/ruta?origen_id=${origenId}&dependencia_id=${dep.id}`);
    if (!res.ok) {
      resultado.innerHTML = `<p class="hint">Esta oficina todavía no tiene una ruta interna cargada. Pregunta en el módulo de orientación.</p>`;
      return;
    }
    const ruta = await res.json();
    const pasos = ruta.pasos
      .filter((p) => p.instruccion)
      .map((p) => `<li>${p.instruccion}</li>`)
      .join("");
    const textoCompleto = ruta.pasos
      .filter((p) => p.instruccion)
      .map((p) => p.instruccion)
      .join(". ");
    // El mapa real (con posiciones) solo existe para el Nivel 1. Para los
    // pisos 4-20 (patrón repetido y documentado, aunque sin datos de qué
    // oficina exacta cae dónde) se muestra en cambio un esquema genérico de
    // "planta típica" -- en cualquier otro caso, el aviso de texto de
    // siempre, sin inventar un dibujo que no corresponde.
    const pisoFinal = ruta.pasos[ruta.pasos.length - 1]?.piso;
    const pisoFinalNum = pisoFinal ? parseInt(pisoFinal, 10) : NaN;
    let mapaVisual = "";
    let avisoAproximada = "";
    if (ruta.pasos.every((p) => p.piso === "1" && p.pos_x != null && p.pos_y != null)) {
      mapaVisual = renderMapaSVG(ruta.pasos);
    } else if (ruta.aproximada && pisoFinalNum >= PISO_TIPICO_MIN && pisoFinalNum <= PISO_TIPICO_MAX) {
      mapaVisual = renderMapaGenericoSVG(pisoFinal, ruta.dependencia_nombre);
    } else if (ruta.aproximada) {
      avisoAproximada = `<p class="hint" style="margin-top:0.5rem;">Esta ruta llega hasta el piso correcto -- una vez ahí, pregunta por "${escaparHtmlPublico(ruta.dependencia_nombre)}".</p>`;
    }
    resultado.innerHTML = `
      ${mapaVisual}
      <ol style="padding-left:1.2rem; margin-top:0.6rem;">${pasos || `<li>Ya estás en el punto más cercano a ${escaparHtmlPublico(ruta.dependencia_nombre)}.</li>`}</ol>
      ${avisoAproximada}
      <button type="button" class="primary" data-leer-ruta style="margin-top:0.4rem;">🔊 Escuchar ruta</button>
    `;
    const textoParaLeer = (textoCompleto || `Ya estás cerca de ${ruta.dependencia_nombre}.`) +
      (ruta.aproximada ? ` Una vez ahí, pregunta por ${ruta.dependencia_nombre}.` : "");
    resultado.querySelector("[data-leer-ruta]").addEventListener("click", () => leerTexto(textoParaLeer));
  } catch {
    resultado.innerHTML = `<p class="hint">No pudimos calcular la ruta. Intenta de nuevo.</p>`;
  }
}

function escaparHtmlPublico(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function tarjetaAccesibilidadSede(sede) {
  const el = document.createElement("article");
  el.className = "card";
  const items = [
    sede.rampa ? "Rampa de acceso" : null,
    sede.ascensor ? "Ascensor" : null,
    sede.banio_accesible ? "Baño accesible" : null,
    sede.estacionamiento_accesible ? "Estacionamiento accesible" : null,
    sede.personal_asistencia ? "Personal de asistencia disponible" : null,
  ].filter(Boolean);
  const texto = items.length
    ? `${sede.nombre} cuenta con: ${items.join(", ")}.`
    : `No tenemos registrada información de accesibilidad confirmada para ${sede.nombre}. Consulta en el módulo de orientación.`;
  el.innerHTML = `
    <div class="card-top">
      <h2>Accesibilidad en ${sede.nombre}</h2>
      <span class="badge servicio">Sede</span>
    </div>
    ${items.length ? `<div class="a11y-row">${items.map((i) => `<span>${i}</span>`).join("")}</div>` : `<p class="meta">${texto}</p>`}
    <div class="card-actions">
      <button class="primary" type="button" data-leer>🔊 Escuchar</button>
    </div>
  `;
  el.querySelector("[data-leer]").addEventListener("click", () => leerTexto(texto));
  return el;
}

// Vuelve a la pantalla de opciones desde cualquier resultado (búsqueda,
// tile, "Estoy aquí" o "Necesito ayuda") -- sin esto, la única forma de
// volver era notar el botón "✕" junto al buscador, que ni siquiera aparece
// cuando se llegó por "Estoy aquí" o "Necesito ayuda" (no tocan ese campo).
function volverAlInicio() {
  const campo = document.getElementById("buscar");
  campo.value = "";
  actualizarBotonLimpiar();
  document.getElementById("panel-estoy-aqui").style.display = "none";
  document.getElementById("resultados").innerHTML = "";
  document.getElementById("feedback-caja").innerHTML = "";
  document.getElementById("estado-vacio").style.display = "block";
}

function botonVolver() {
  const p = document.createElement("p");
  p.style.marginBottom = "0.8rem";
  p.innerHTML = `<button type="button" class="btn secondary" id="btn-volver-opciones">← Volver a las opciones</button>`;
  p.querySelector("button").addEventListener("click", volverAlInicio);
  return p;
}

function tarjetaFichaSede(sede, total) {
  const el = document.createElement("article");
  el.className = "card";
  el.innerHTML = `
    <div class="card-top">
      <h2>${sede.nombre}</h2>
      <span class="badge servicio">Sede</span>
    </div>
    ${sede.direccion ? `<p class="meta"><strong>Dirección:</strong> ${sede.direccion}</p>` : ""}
    ${sede.horario_atencion ? `<p class="meta"><strong>Horario:</strong> ${sede.horario_atencion}</p>` : ""}
    ${sede.telefono ? `<p class="meta"><strong>Teléfono:</strong> ${sede.telefono}</p>` : ""}
    <p class="meta">${total} dependencia${total === 1 ? "" : "s"} publicada${total === 1 ? "" : "s"} en esta sede.</p>
  `;
  return el;
}

// ── "Estoy aquí": el ciudadano elige su sede y ve todo lo publicado en ella,
// sin tener que escribir ni hablar una búsqueda ──
async function cargarSedesParaSelector() {
  const sel = document.getElementById("select-sede");
  if (!sel) return;
  try {
    const sedes = await (await fetch(`${API}/sedes`)).json();
    sel.innerHTML = sedes.map((s) => `<option value="${s.id}">${s.nombre}</option>`).join("");
    if (sedeContextoId) sel.value = String(sedeContextoId);
  } catch {
    sel.innerHTML = '<option value="">No se pudo cargar la lista de sedes</option>';
  }
}

async function mostrarDependenciasDeSede(sedeId) {
  const cont = document.getElementById("resultados");
  const feedback = document.getElementById("feedback-caja");
  document.getElementById("estado-vacio").style.display = "none";
  feedback.innerHTML = "";
  cont.innerHTML = "";
  cont.appendChild(botonVolver());
  const cargando = document.createElement("p");
  cargando.className = "hint";
  cargando.textContent = "Buscando…";
  cont.appendChild(cargando);
  try {
    const [sedes, deps] = await Promise.all([
      fetch(`${API}/sedes`).then((r) => r.json()),
      fetch(`${API}/sedes/${sedeId}/dependencias`).then((r) => r.json()),
    ]);
    const sede = sedes.find((s) => String(s.id) === String(sedeId));
    cargando.remove();
    if (sede) cont.appendChild(tarjetaFichaSede(sede, deps.length));
    if (!deps.length) {
      const aviso = document.createElement("div");
      aviso.className = "fallback";
      aviso.setAttribute("role", "status");
      aviso.textContent = "Todavía no hay dependencias publicadas para esta sede en el sistema. Prueba con el buscador de arriba o acércate al módulo de orientación.";
      cont.appendChild(aviso);
      return;
    }
    deps.forEach((dep) => cont.appendChild(tarjeta(dep)));
  } catch {
    cargando.remove();
    const aviso = document.createElement("div");
    aviso.className = "fallback";
    aviso.innerHTML = "<strong>No pudimos conectar con el servidor.</strong> Intenta nuevamente en unos segundos.";
    cont.appendChild(aviso);
  }
}

document.getElementById("tile-estoy-aqui").addEventListener("click", () => {
  const panel = document.getElementById("panel-estoy-aqui");
  panel.style.display = panel.style.display === "none" ? "block" : "none";
});
document.getElementById("btn-ver-sede").addEventListener("click", () => {
  const sel = document.getElementById("select-sede");
  if (sel.value) mostrarDependenciasDeSede(sel.value);
});

// ── "Necesito ayuda": salida siempre disponible a orientación humana, sin
// depender de que el catálogo tenga cargada y publicada la información del
// MAU de cada sede todavía ──
function mostrarNecesitoAyuda() {
  const cont = document.getElementById("resultados");
  const feedback = document.getElementById("feedback-caja");
  document.getElementById("estado-vacio").style.display = "none";
  document.getElementById("panel-estoy-aqui").style.display = "none";
  feedback.innerHTML = "";
  cont.innerHTML = "";
  cont.appendChild(botonVolver());
  cont.insertAdjacentHTML("beforeend", `
    <article class="card">
      <div class="card-top">
        <h2>Necesito ayuda</h2>
        <span class="badge servicio">Orientación humana</span>
      </div>
      <p class="meta">¿No sabes qué necesitas, o prefieres que una persona te oriente directamente?</p>
      <ul class="meta" style="padding-left:1.1rem;">
        <li>Acércate al <strong>Módulo de Atención al Usuario (MAU)</strong>, ubicado en el ingreso de tu sede.</li>
        <li>O escribe al canal institucional de atención al ciudadano de la Corte.</li>
        <li>También puedes usar el buscador de arriba, o el botón "Estoy aquí" si ya sabes en qué sede estás.</li>
      </ul>
      <div class="card-actions">
        <a href="/api/v1/directorio.pdf" target="_blank" rel="noopener">Descargar directorio completo (PDF)</a>
      </div>
    </article>
  `);
}
document.getElementById("tile-necesito-ayuda").addEventListener("click", mostrarNecesitoAyuda);

// ── Retroalimentación ──
function renderFeedback(consultaId) {
  const box = document.getElementById("feedback-caja");
  if (!consultaId) {
    box.innerHTML = "";
    return;
  }
  box.innerHTML = `
    <div class="feedback">
      <p>¿Esto te resultó útil?</p>
      <div class="opciones">
        <button type="button" data-valor="si">🙂 Sí</button>
        <button type="button" data-valor="parcial">😐 Parcialmente</button>
        <button type="button" data-valor="no">🙁 No</button>
      </div>
    </div>
  `;
  box.querySelectorAll("[data-valor]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await fetch(`${API}/satisfaccion/${consultaId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ valor: btn.dataset.valor }),
        });
      } catch (e) {
        // el agradecimiento se muestra igual; esto es retroalimentación opcional,
        // no bloquea nada si la red falla.
      }
      box.innerHTML = '<div class="feedback"><p class="gracias">Gracias por avisarnos.</p></div>';
    });
  });
}

// Contexto conocido de la sesión: llega por ?sede= o ?dependencia= en la URL.
let sedeContextoId = null;

// El enlace de descarga sigue el mismo contexto de sede que el saludo: si la
// persona llegó por el QR de una sede o de una dependencia, el PDF que se
// lleva es el de esa sede, no el directorio completo de las 25.
function actualizarEnlaceDirectorio() {
  const enlace = document.getElementById("link-directorio-pdf");
  if (!enlace) return;
  enlace.href = sedeContextoId ? `${API}/directorio.pdf?sede_id=${sedeContextoId}` : `${API}/directorio.pdf`;
}

// El indicador de "modo accesible" es de la sesión (contraste/texto/tema),
// no de la búsqueda puntual -- se calcula al momento de cada consulta.
function modoAccesibleActivo() {
  return (
    root.getAttribute("data-contrast") === "alto" ||
    fontStep !== 0 ||
    temaEfectivoEsOscuro()
  );
}

async function buscarYRenderizar(q, opciones = {}) {
  const cont = document.getElementById("resultados");
  const vacio = document.getElementById("estado-vacio");
  const feedback = document.getElementById("feedback-caja");

  if (!q.trim()) {
    cont.innerHTML = "";
    feedback.innerHTML = "";
    vacio.style.display = "block";
    return;
  }
  vacio.style.display = "none";
  cont.innerHTML = `<p class="hint">Buscando…</p>`;
  feedback.innerHTML = "";
  try {
    const params = new URLSearchParams({ q });
    if (sedeContextoId) params.set("sede_contexto", sedeContextoId);
    if (modoAccesibleActivo()) params.set("modo_accesible", "true");
    if (opciones.viaVoz) params.set("via_voz", "true");

    const res = await fetch(`${API}/buscar?${params.toString()}`);
    const data = await res.json();
    cont.innerHTML = "";
    cont.appendChild(botonVolver());
    if (data.sede_accesibilidad) {
      cont.appendChild(tarjetaAccesibilidadSede(data.sede_accesibilidad));
    }
    if (data.fallback || data.resultados.length === 0) {
      if (!data.sede_accesibilidad) {
        cont.insertAdjacentHTML("beforeend", `
          <div class="fallback" role="status">
            <strong>${data.mensaje || "No podemos identificar con seguridad lo que buscas. Acércate al módulo de orientación en el ingreso o escribe al canal institucional de atención."}</strong>
          </div>`);
      }
      renderFeedback(data.consulta_id);
      return;
    }
    data.resultados.forEach((dep) => cont.appendChild(tarjeta(dep)));
    renderFeedback(data.consulta_id);
  } catch (e) {
    cont.innerHTML = "";
    cont.appendChild(botonVolver());
    cont.insertAdjacentHTML("beforeend", `<div class="fallback"><strong>No pudimos conectar con el servidor.</strong> Intenta nuevamente en unos segundos.</div>`);
  }
}

document.getElementById("form-buscar").addEventListener("submit", (e) => {
  e.preventDefault();
  buscarYRenderizar(document.getElementById("buscar").value);
});

const btnLimpiar = document.getElementById("btn-limpiar");
function actualizarBotonLimpiar() {
  btnLimpiar.style.display = document.getElementById("buscar").value ? "" : "none";
}
let debounce;
document.getElementById("buscar").addEventListener("input", (e) => {
  actualizarBotonLimpiar();
  clearTimeout(debounce);
  debounce = setTimeout(() => buscarYRenderizar(e.target.value), 300);
});
btnLimpiar.addEventListener("click", () => {
  const campo = document.getElementById("buscar");
  campo.value = "";
  actualizarBotonLimpiar();
  buscarYRenderizar("");
  campo.focus();
});

// ── Entrada por voz (reconocimiento de habla) ──
(function configurarVoz() {
  const btnVoz = document.getElementById("btn-voz");
  const estado = document.getElementById("voz-estado");
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    btnVoz.disabled = true;
    btnVoz.title = "El reconocimiento de voz no está disponible en este navegador.";
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "es-PE";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  let escuchando = false;

  recognition.addEventListener("result", (e) => {
    const texto = e.results[0][0].transcript;
    document.getElementById("buscar").value = texto;
    actualizarBotonLimpiar();
    buscarYRenderizar(texto, { viaVoz: true });
    estado.textContent = `Escuché: "${texto}"`;
  });
  recognition.addEventListener("error", (e) => {
    const mensajes = {
      "not-allowed": "Permiso de micrófono denegado.",
      "no-speech": "No se detectó voz, intenta de nuevo.",
      "audio-capture": "No se encontró un micrófono disponible.",
    };
    estado.textContent = mensajes[e.error] || "No se pudo usar el micrófono.";
  });
  recognition.addEventListener("end", () => {
    escuchando = false;
    btnVoz.setAttribute("aria-pressed", "false");
  });

  btnVoz.addEventListener("click", () => {
    if (escuchando) {
      recognition.stop();
      return;
    }
    estado.textContent = "Escuchando…";
    btnVoz.setAttribute("aria-pressed", "true");
    escuchando = true;
    try {
      recognition.start();
    } catch {
      escuchando = false;
      btnVoz.setAttribute("aria-pressed", "false");
    }
  });
})();

// ── Saludo contextual al llegar desde un QR de sede o dependencia
// (?sede=<id> / ?dependencia=<id>) ──
(async function saludoContextual() {
  const params = new URLSearchParams(window.location.search);
  const sedeId = params.get("sede");
  const depId = params.get("dependencia");
  const banner = document.getElementById("banner-contexto");

  if (depId) {
    try {
      const dep = await (await fetch(`${API}/dependencias/${depId}`)).json();
      if (dep && dep.sede) {
        sedeContextoId = dep.sede.id;
        actualizarEnlaceDirectorio();
        banner.textContent = `Estás consultando información de "${dep.nombre}", en ${dep.sede.nombre}.`;
        banner.classList.add("visible");
        const cont = document.getElementById("resultados");
        document.getElementById("estado-vacio").style.display = "none";
        cont.appendChild(tarjeta(dep));
      }
    } catch {
      // sin conexión: la búsqueda normal sigue funcionando igual.
    }
    return;
  }

  if (!sedeId) return;
  try {
    const sedes = await (await fetch(`${API}/sedes`)).json();
    const sede = sedes.find((s) => String(s.id) === sedeId);
    if (!sede) return;
    sedeContextoId = sede.id;
    actualizarEnlaceDirectorio();
    const nombre = /^sede\s/i.test(sede.nombre) ? sede.nombre : `sede ${sede.nombre}`;
    banner.textContent = `Estás consultando información de la ${nombre}. ¿Qué necesitas encontrar?`;
    banner.classList.add("visible");
  } catch {
    // sin conexión al listar sedes: la búsqueda normal sigue funcionando igual.
  }
})();

// ── Accesibilidad (persistida en el navegador del ciudadano) ──
const root = document.documentElement;
let fontStep = parseInt(localStorage.getItem("jo_fontStep") || "0", 10);
root.style.setProperty("--fs", (16 + fontStep * 2.5) + "px");
if (localStorage.getItem("jo_contraste") === "alto") root.setAttribute("data-contrast", "alto");

// El tema puede venir del sistema (prefers-color-scheme) sin que haya ningún
// atributo explícito todavía -- hay que tenerlo en cuenta como "oscuro
// efectivo", si no, el primer clic en el botón solo confirma el oscuro
// implícito en vez de cambiar a claro.
function temaEfectivoEsOscuro() {
  const attr = root.getAttribute("data-theme");
  if (attr === "dark") return true;
  if (attr === "light") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}
const prefTema = localStorage.getItem("jo_tema");
if (prefTema === "dark" || prefTema === "light") root.setAttribute("data-theme", prefTema);
document.getElementById("btn-tema").setAttribute("aria-pressed", String(temaEfectivoEsOscuro()));

document.getElementById("btn-mas").addEventListener("click", () => {
  fontStep = Math.min(fontStep + 1, 3);
  root.style.setProperty("--fs", (16 + fontStep * 2.5) + "px");
  localStorage.setItem("jo_fontStep", fontStep);
});
document.getElementById("btn-menos").addEventListener("click", () => {
  fontStep = Math.max(fontStep - 1, -1);
  root.style.setProperty("--fs", (16 + fontStep * 2.5) + "px");
  localStorage.setItem("jo_fontStep", fontStep);
});
document.getElementById("btn-contraste").addEventListener("click", (e) => {
  const on = root.getAttribute("data-contrast") === "alto";
  root.setAttribute("data-contrast", on ? "normal" : "alto");
  localStorage.setItem("jo_contraste", on ? "normal" : "alto");
  e.target.setAttribute("aria-pressed", String(!on));
});
document.getElementById("btn-tema").addEventListener("click", (e) => {
  const oscuroAhora = temaEfectivoEsOscuro();
  const nuevo = oscuroAhora ? "light" : "dark";
  root.setAttribute("data-theme", nuevo);
  localStorage.setItem("jo_tema", nuevo);
  e.target.setAttribute("aria-pressed", String(!oscuroAhora));
});

cargarSedesParaSelector();
