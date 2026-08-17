const API = "/api";
let TOKEN = sessionStorage.getItem("jo_token");
let USUARIO = null;

function headers(json = true) {
  const h = {};
  if (TOKEN) h["Authorization"] = `Bearer ${TOKEN}`;
  if (json) h["Content-Type"] = "application/json";
  return h;
}

async function api(path, opts = {}) {
  const res = await fetch(API + path, { ...opts, headers: { ...headers(opts.jsonBody !== false), ...(opts.headers || {}) } });
  if (res.status === 401) {
    cerrarSesion();
    throw new Error("Sesión expirada");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error desconocido" }));
    throw new Error(err.detail || "Error en la solicitud");
  }
  return res.status === 204 ? null : res.json();
}

function mostrarApp() {
  document.getElementById("vista-login").style.display = "none";
  document.getElementById("vista-app").style.display = "block";
  document.getElementById("who").textContent = `${USUARIO.nombre} · ${USUARIO.rol}${USUARIO.area ? " · " + USUARIO.area : ""}`;
  if (USUARIO.rol === "admin") document.getElementById("panel-auditoria").style.display = "block";
  cargarTodo();
}

function mostrarLogin(mensaje) {
  document.getElementById("vista-login").style.display = "block";
  document.getElementById("vista-app").style.display = "none";
  document.getElementById("login-error").innerHTML = mensaje ? `<p class="error-msg">${mensaje}</p>` : "";
}

function cerrarSesion() {
  TOKEN = null;
  USUARIO = null;
  sessionStorage.removeItem("jo_token");
  mostrarLogin();
}

async function iniciar() {
  if (!TOKEN) return mostrarLogin();
  try {
    USUARIO = await api("/auth/yo");
    mostrarApp();
  } catch {
    cerrarSesion();
  }
}

document.getElementById("form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const pass = document.getElementById("login-pass").value;
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", pass);
  try {
    const res = await fetch(API + "/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Correo o contraseña incorrectos" }));
      throw new Error(err.detail);
    }
    const data = await res.json();
    TOKEN = data.access_token;
    USUARIO = data.usuario;
    sessionStorage.setItem("jo_token", TOKEN);
    mostrarApp();
  } catch (err) {
    mostrarLogin(err.message);
  }
});

document.getElementById("btn-logout").addEventListener("click", cerrarSesion);

// ── Estadísticas ──
async function cargarStats() {
  const s = await api("/admin/metricas/resumen");
  const box = document.getElementById("stats");
  box.innerHTML = "";
  const items = [
    [s.total_consultas, "Consultas totales"],
    [s.consultas_resueltas, "Resueltas"],
    [s.consultas_sin_resultado, "Sin resultado"],
    [s.porcentaje_resueltas !== null ? s.porcentaje_resueltas + "%" : "—", "% de acierto"],
  ];
  for (const [n, l] of items) {
    const d = document.createElement("div");
    d.className = "stat";
    d.innerHTML = `<div class="n">${n}</div><div class="l">${l}</div>`;
    box.appendChild(d);
  }
}

// ── Tabla de dependencias ──
let CACHE_DEPS = [];

function estadoBadge(estado) {
  return `<span class="badge ${estado}">${estado}</span>`;
}

async function cargarDependencias() {
  CACHE_DEPS = await api("/admin/dependencias");
  const tbody = document.querySelector("#tabla-dependencias tbody");
  tbody.innerHTML = "";
  for (const d of CACHE_DEPS) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${d.nombre}</td>
      <td>${d.tipo}</td>
      <td>${d.sede || "—"}${d.piso ? " · piso " + d.piso : ""}</td>
      <td>${estadoBadge(d.estado)}</td>
      <td class="actions">
        <button class="btn secondary" data-editar="${d.id}">Editar</button>
        <button class="btn secondary" data-desactivar="${d.id}">Desactivar</button>
      </td>`;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll("[data-editar]").forEach((b) =>
    b.addEventListener("click", () => cargarEnFormulario(parseInt(b.dataset.editar)))
  );
  tbody.querySelectorAll("[data-desactivar]").forEach((b) =>
    b.addEventListener("click", () => desactivar(parseInt(b.dataset.desactivar)))
  );
}

async function desactivar(id) {
  if (!confirm("¿Desactivar esta dependencia? Dejará de verse en el sitio público.")) return;
  await api(`/admin/dependencias/${id}`, { method: "DELETE" });
  await Promise.all([cargarDependencias(), cargarStats()]);
}

function limpiarFormulario() {
  document.getElementById("form-titulo").textContent = "Nueva dependencia";
  document.getElementById("f-id").value = "";
  document.getElementById("form-dep").reset();
  document.getElementById("f-estado").value = "revision";
  if (USUARIO.rol !== "admin" && USUARIO.area) {
    document.getElementById("f-area").value = USUARIO.area;
  }
  document.getElementById("form-error").innerHTML = "";
}

function cargarEnFormulario(id) {
  const d = CACHE_DEPS.find((x) => x.id === id);
  if (!d) return;
  document.getElementById("form-titulo").textContent = `Editar: ${d.nombre}`;
  document.getElementById("f-id").value = d.id;
  document.getElementById("f-nombre").value = d.nombre || "";
  document.getElementById("f-alias").value = (d.alias || []).join(", ");
  document.getElementById("f-tipo").value = d.tipo;
  document.getElementById("f-area").value = d.area || "";
  document.getElementById("f-categoria").value = d.categoria || "";
  document.getElementById("f-sede").value = d.sede || "";
  document.getElementById("f-piso").value = d.piso || "";
  document.getElementById("f-oficina").value = d.oficina || "";
  document.getElementById("f-horario").value = d.horario || "";
  document.getElementById("f-servicios").value = d.servicios || "";
  document.getElementById("f-requisitos").value = d.requisitos || "";
  document.getElementById("f-telefono").value = d.telefono || "";
  document.getElementById("f-correo").value = d.correo || "";
  document.getElementById("f-rampa").checked = !!d.rampa;
  document.getElementById("f-ascensor").checked = !!d.ascensor;
  document.getElementById("f-banio").checked = !!d.banio_accesible;
  document.getElementById("f-ruta").checked = !!d.ruta_accesible;
  document.getElementById("f-estado").value = d.estado;
  document.getElementById("f-responsable").value = d.responsable_validar || "";
  window.scrollTo({ top: document.getElementById("form-dep").offsetTop - 20, behavior: "smooth" });
}

document.getElementById("btn-cancelar").addEventListener("click", limpiarFormulario);

document.getElementById("form-dep").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("f-id").value;
  const payload = {
    nombre: document.getElementById("f-nombre").value,
    alias: document.getElementById("f-alias").value,
    tipo: document.getElementById("f-tipo").value,
    area: document.getElementById("f-area").value,
    categoria: document.getElementById("f-categoria").value || null,
    sede: document.getElementById("f-sede").value || null,
    piso: document.getElementById("f-piso").value || null,
    oficina: document.getElementById("f-oficina").value || null,
    horario: document.getElementById("f-horario").value || null,
    servicios: document.getElementById("f-servicios").value || null,
    requisitos: document.getElementById("f-requisitos").value || null,
    telefono: document.getElementById("f-telefono").value || null,
    correo: document.getElementById("f-correo").value || null,
    rampa: document.getElementById("f-rampa").checked,
    ascensor: document.getElementById("f-ascensor").checked,
    banio_accesible: document.getElementById("f-banio").checked,
    ruta_accesible: document.getElementById("f-ruta").checked,
    estado: document.getElementById("f-estado").value,
    responsable_validar: document.getElementById("f-responsable").value || null,
  };
  try {
    if (id) {
      await api(`/admin/dependencias/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    } else {
      await api("/admin/dependencias", { method: "POST", body: JSON.stringify(payload) });
    }
    limpiarFormulario();
    await Promise.all([cargarDependencias(), cargarStats(), cargarAuditoria()]);
  } catch (err) {
    document.getElementById("form-error").innerHTML = `<p class="error-msg">${err.message}</p>`;
  }
});

// ── Auditoría (solo admin) ──
async function cargarAuditoria() {
  if (USUARIO.rol !== "admin") return;
  const registros = await api("/admin/auditoria");
  const tbody = document.querySelector("#tabla-auditoria tbody");
  tbody.innerHTML = "";
  for (const r of registros) {
    const tr = document.createElement("tr");
    const fecha = new Date(r.fecha).toLocaleString("es-PE");
    tr.innerHTML = `<td>${fecha}</td><td>${r.usuario_email || "—"}</td><td>${r.accion}</td><td>${r.detalle || ""}</td>`;
    tbody.appendChild(tr);
  }
}

async function cargarTodo() {
  limpiarFormulario();
  await Promise.all([cargarStats(), cargarDependencias(), cargarAuditoria()]);
}

iniciar();
