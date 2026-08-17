const API = "/api/v1";

const EJEMPLOS = [
  "11.º Juzgado Civil",
  "Recursos Humanos",
  "mi computadora no funciona",
  "presentar un documento",
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

function badgeLabel(tipo) {
  return { jurisdiccional: "Jurisdiccional", administrativa: "Administrativa", servicio: "Servicio" }[tipo] || tipo;
}

function leerEnVozAlta(dep) {
  if (!("speechSynthesis" in window)) {
    alert("La lectura en voz alta no está disponible en este navegador.");
    return;
  }
  const partes = [
    `${dep.nombre}.`,
    dep.sede ? `Se encuentra en ${dep.sede.nombre}` : "",
    dep.piso ? `, piso ${dep.piso}` : "",
    dep.oficina && dep.oficina !== "—" ? `, oficina ${dep.oficina}.` : ".",
    dep.horario ? `Horario: ${dep.horario}.` : "",
    dep.ruta_accesible ? "Cuenta con ruta accesible." : "",
  ];
  const u = new SpeechSynthesisUtterance(partes.join(" "));
  u.lang = "es-PE";
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

function tarjeta(dep) {
  const el = document.createElement("article");
  el.className = "card";
  const nombreSede = dep.sede ? dep.sede.nombre : null;
  const direccion = (dep.sede && dep.sede.direccion) || [nombreSede, "Cercado de Lima"].filter(Boolean).join(", ");
  const osmQuery = encodeURIComponent(direccion || nombreSede || dep.nombre);
  const accesible = dep.rampa || dep.ascensor || dep.banio_accesible || (dep.sede && (dep.sede.rampa || dep.sede.ascensor || dep.sede.banio_accesible));

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

async function buscarYRenderizar(q) {
  const cont = document.getElementById("resultados");
  if (!q.trim()) {
    cont.innerHTML = "";
    return;
  }
  cont.innerHTML = `<p class="hint">Buscando…</p>`;
  try {
    const res = await fetch(`${API}/buscar?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    cont.innerHTML = "";
    if (data.fallback || data.resultados.length === 0) {
      cont.innerHTML = `
        <div class="fallback" role="status">
          <strong>No podemos identificar con seguridad lo que buscas.</strong>
          ${data.mensaje || "Acércate al módulo de orientación en el ingreso o escribe al canal institucional de atención."}
        </div>`;
      return;
    }
    data.resultados.forEach((dep) => cont.appendChild(tarjeta(dep)));
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

// ── Accesibilidad (persistida en el navegador del ciudadano) ──
const root = document.documentElement;
let fontStep = parseInt(localStorage.getItem("jo_fontStep") || "0", 10);
root.style.setProperty("--fs", (16 + fontStep * 2.5) + "px");
if (localStorage.getItem("jo_contraste") === "alto") root.setAttribute("data-contrast", "alto");
if (localStorage.getItem("jo_tema") === "dark") root.setAttribute("data-theme", "dark");

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
  const on = root.getAttribute("data-theme") === "dark";
  root.setAttribute("data-theme", on ? "light" : "dark");
  localStorage.setItem("jo_tema", on ? "light" : "dark");
  e.target.setAttribute("aria-pressed", String(!on));
});
