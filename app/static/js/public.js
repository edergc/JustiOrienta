const API = "/api/v1";

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
    buscarYRenderizar(ej);
    document.getElementById("buscar").focus();
  });
  chipsBox.appendChild(b);
});

document.querySelectorAll(".tile-btn").forEach((b) => {
  b.addEventListener("click", () => {
    document.getElementById("buscar").value = b.dataset.ej;
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
  const partes = [
    `${dep.nombre}.`,
    dep.sede ? `Se encuentra en ${dep.sede.nombre}` : "",
    dep.piso ? `, piso ${dep.piso}` : "",
    dep.oficina && dep.oficina !== "—" ? `, oficina ${dep.oficina}.` : ".",
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

  const servicios = (dep.servicios_detalle || [])
    .map((s) => `<li><strong>${s.nombre}</strong>${s.requisitos ? " — " + s.requisitos : ""}</li>`)
    .join("");

  el.innerHTML = `
    <div class="card-top">
      <h2>${dep.nombre}</h2>
      <span class="badge ${dep.tipo}">${badgeLabel(dep.tipo)}</span>
    </div>
    <p class="meta"><strong>${nombreSede || "Sede no registrada"}</strong>${dep.piso ? " — Piso " + dep.piso : ""}${dep.oficina ? ", oficina " + dep.oficina : ""}</p>
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
      <a href="https://www.openstreetmap.org/search?query=${osmQuery}" target="_blank" rel="noopener">Cómo llegar (OpenStreetMap)</a>
    </div>
  `;
  el.querySelector("[data-leer]").addEventListener("click", () => leerEnVozAlta(dep));
  return el;
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
    if (data.sede_accesibilidad) {
      cont.appendChild(tarjetaAccesibilidadSede(data.sede_accesibilidad));
    }
    if (data.fallback || data.resultados.length === 0) {
      if (!data.sede_accesibilidad) {
        cont.innerHTML = `
          <div class="fallback" role="status">
            <strong>No podemos identificar con seguridad lo que buscas.</strong>
            ${data.mensaje || "Acércate al módulo de orientación en el ingreso o escribe al canal institucional de atención."}
          </div>`;
      }
      renderFeedback(data.consulta_id);
      return;
    }
    data.resultados.forEach((dep) => cont.appendChild(tarjeta(dep)));
    renderFeedback(data.consulta_id);
  } catch (e) {
    cont.innerHTML = `<div class="fallback"><strong>No pudimos conectar con el servidor.</strong> Intenta nuevamente en unos segundos.</div>`;
  }
}

document.getElementById("form-buscar").addEventListener("submit", (e) => {
  e.preventDefault();
  buscarYRenderizar(document.getElementById("buscar").value);
});
let debounce;
document.getElementById("buscar").addEventListener("input", (e) => {
  clearTimeout(debounce);
  debounce = setTimeout(() => buscarYRenderizar(e.target.value), 300);
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
