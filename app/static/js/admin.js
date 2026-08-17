const API = "/api/v1";
let TOKEN = sessionStorage.getItem("jo_token");
let USUARIO = null;
let CACHE_DEPS = [];
let CACHE_SEDES = [];

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

function esAdmin() { return USUARIO && USUARIO.rol === "admin"; }
function puedeLeerAuditoria() { return USUARIO && (USUARIO.rol === "admin" || USUARIO.rol === "auditor"); }
function puedeAprobar(dep) {
  if (!USUARIO) return false;
  if (USUARIO.rol === "admin") return true;
  return USUARIO.rol === "validador" && USUARIO.area === dep.area;
}

function mostrarApp() {
  document.getElementById("vista-login").style.display = "none";
  document.getElementById("vista-app").style.display = "block";
  document.getElementById("who").textContent = `${USUARIO.nombre} · ${USUARIO.rol}${USUARIO.area ? " · " + USUARIO.area : ""}`;

  document.querySelector('[data-tab="tab-sedes"]').style.display = esAdmin() ? "" : "none";
  document.querySelector('[data-tab="tab-usuarios"]').style.display = esAdmin() ? "" : "none";
  document.querySelector('[data-tab="tab-auditoria"]').style.display = puedeLeerAuditoria() ? "" : "none";

  // Siempre arrancar en "Dependencias": evita que quede activa una pestaña
  // que la sesión anterior dejó abierta y que este rol ya no puede ver.
  document.querySelectorAll(".tab-btn").forEach((b) => b.setAttribute("aria-pressed", "false"));
  document.querySelectorAll(".tab-panel").forEach((p) => (p.style.display = "none"));
  document.querySelector('[data-tab="tab-dependencias"]').setAttribute("aria-pressed", "true");
  document.getElementById("tab-dependencias").style.display = "block";

  poblarOpcionesEstado();
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

// ── Pestañas ──
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.setAttribute("aria-pressed", "false"));
    document.querySelectorAll(".tab-panel").forEach((p) => (p.style.display = "none"));
    btn.setAttribute("aria-pressed", "true");
    document.getElementById(btn.dataset.tab).style.display = "block";
  });
});

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

// ═══════════════════════════════════════════════════════════
// SEDES
// ═══════════════════════════════════════════════════════════
async function cargarSedes() {
  CACHE_SEDES = await api("/admin/sedes");

  const tbody = document.querySelector("#tabla-sedes tbody");
  tbody.innerHTML = "";
  for (const s of CACHE_SEDES) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${s.nombre}</td><td>${s.direccion || "—"}</td><td>${estadoBadge(s.estado)}</td>
      <td>${esAdmin() ? `<button class="btn secondary" data-editar-sede="${s.id}">Editar</button>` : ""}</td>`;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll("[data-editar-sede]").forEach((b) =>
    b.addEventListener("click", () => cargarSedeEnFormulario(parseInt(b.dataset.editarSede)))
  );

  const selSede = document.getElementById("f-sede");
  const actual = selSede.value;
  selSede.innerHTML = CACHE_SEDES.map((s) => `<option value="${s.id}">${s.nombre}</option>`).join("");
  if (actual) selSede.value = actual;
}

function limpiarFormularioSede() {
  document.getElementById("form-sede-titulo").textContent = "Nueva sede";
  document.getElementById("s-id").value = "";
  document.getElementById("form-sede").reset();
  document.getElementById("form-sede-error").innerHTML = "";
}

function cargarSedeEnFormulario(id) {
  const s = CACHE_SEDES.find((x) => x.id === id);
  if (!s) return;
  document.getElementById("form-sede-titulo").textContent = `Editar: ${s.nombre}`;
  document.getElementById("s-id").value = s.id;
  document.getElementById("s-nombre").value = s.nombre || "";
  document.getElementById("s-direccion").value = s.direccion || "";
  document.getElementById("s-referencia").value = s.referencia || "";
  document.getElementById("s-horario").value = s.horario_atencion || "";
  document.getElementById("s-telefono").value = s.telefono || "";
  document.getElementById("s-rampa").checked = !!s.rampa;
  document.getElementById("s-ascensor").checked = !!s.ascensor;
  document.getElementById("s-banio").checked = !!s.banio_accesible;
  document.getElementById("s-estacionamiento").checked = !!s.estacionamiento_accesible;
  document.getElementById("s-asistencia").checked = !!s.personal_asistencia;
}

document.getElementById("btn-sede-cancelar").addEventListener("click", limpiarFormularioSede);

document.getElementById("form-sede").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("s-id").value;
  const payload = {
    nombre: document.getElementById("s-nombre").value,
    direccion: document.getElementById("s-direccion").value || null,
    referencia: document.getElementById("s-referencia").value || null,
    horario_atencion: document.getElementById("s-horario").value || null,
    telefono: document.getElementById("s-telefono").value || null,
    rampa: document.getElementById("s-rampa").checked,
    ascensor: document.getElementById("s-ascensor").checked,
    banio_accesible: document.getElementById("s-banio").checked,
    estacionamiento_accesible: document.getElementById("s-estacionamiento").checked,
    personal_asistencia: document.getElementById("s-asistencia").checked,
    estado: "activo",
  };
  try {
    if (id) await api(`/admin/sedes/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    else await api("/admin/sedes", { method: "POST", body: JSON.stringify(payload) });
    limpiarFormularioSede();
    await cargarSedes();
  } catch (err) {
    document.getElementById("form-sede-error").innerHTML = `<p class="error-msg">${err.message}</p>`;
  }
});

// Edificios según la sede elegida en el formulario de dependencia
document.getElementById("f-sede").addEventListener("change", async (e) => {
  await cargarEdificios(e.target.value);
});

async function cargarEdificios(sedeId) {
  const sel = document.getElementById("f-edificio");
  sel.innerHTML = '<option value="">— Ninguno —</option>';
  if (!sedeId) return;
  const edificios = await api(`/admin/edificios?sede_id=${sedeId}`);
  for (const ed of edificios) {
    const opt = document.createElement("option");
    opt.value = ed.id;
    opt.textContent = ed.nombre;
    sel.appendChild(opt);
  }
}

// ═══════════════════════════════════════════════════════════
// USUARIOS (solo admin)
// ═══════════════════════════════════════════════════════════
async function cargarUsuarios() {
  if (!esAdmin()) return;
  const usuarios = await api("/admin/usuarios");
  const tbody = document.querySelector("#tabla-usuarios tbody");
  tbody.innerHTML = "";
  for (const u of usuarios) {
    const tr = document.createElement("tr");
    const ultimo = u.ultimo_acceso ? new Date(u.ultimo_acceso).toLocaleString("es-PE") : "Nunca";
    tr.innerHTML = `<td>${u.nombre}</td><td>${u.email}</td><td>${u.rol}</td><td>${u.area || "—"}</td><td>${ultimo}</td>`;
    tbody.appendChild(tr);
  }
}

document.getElementById("form-usuario").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    nombre: document.getElementById("u-nombre").value,
    email: document.getElementById("u-email").value,
    password: document.getElementById("u-password").value,
    rol: document.getElementById("u-rol").value,
    area: document.getElementById("u-area").value || null,
  };
  try {
    await api("/admin/usuarios", { method: "POST", body: JSON.stringify(payload) });
    document.getElementById("form-usuario").reset();
    document.getElementById("form-usuario-error").innerHTML = "";
    await cargarUsuarios();
  } catch (err) {
    document.getElementById("form-usuario-error").innerHTML = `<p class="error-msg">${err.message}</p>`;
  }
});

// ═══════════════════════════════════════════════════════════
// DEPENDENCIAS
// ═══════════════════════════════════════════════════════════
function estadoBadge(estado) {
  const etiquetas = { activo: "Activo", revision: "En revisión", inactivo: "Inactivo" };
  return `<span class="badge ${estado}">${etiquetas[estado] || estado}</span>`;
}

function poblarOpcionesEstado() {
  const sel = document.getElementById("f-estado");
  const opciones = [
    { v: "revision", t: "En revisión (no visible al público)" },
    { v: "activo", t: "Activo (visible al público)" },
    { v: "inactivo", t: "Inactivo" },
  ];
  sel.innerHTML = opciones
    .map((o) => {
      // Un(a) gestor(a) puede ver que algo está "Activo" pero no elegirlo a
      // mano: cualquier guardado suyo vuelve el contenido a revisión.
      const bloqueada = o.v === "activo" && USUARIO.rol === "gestor";
      return `<option value="${o.v}" ${bloqueada ? "disabled" : ""}>${o.t}${bloqueada ? " — requiere aprobación" : ""}</option>`;
    })
    .join("");
}

async function cargarDependencias() {
  const estado = document.getElementById("filtro-estado").value;
  const qs = estado ? `?estado=${estado}` : "";
  CACHE_DEPS = await api(`/admin/dependencias${qs}`);
  const tbody = document.querySelector("#tabla-dependencias tbody");
  tbody.innerHTML = "";
  for (const d of CACHE_DEPS) {
    const tr = document.createElement("tr");
    const nombreSede = d.sede ? d.sede.nombre : "—";
    tr.innerHTML = `
      <td>${d.nombre}</td>
      <td>${d.tipo}</td>
      <td>${nombreSede}${d.piso ? " · piso " + d.piso : ""}</td>
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
document.getElementById("filtro-estado").addEventListener("change", cargarDependencias);

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
  document.getElementById("f-edificio").innerHTML = '<option value="">— Ninguno —</option>';
  if (USUARIO.rol !== "admin" && USUARIO.area) {
    document.getElementById("f-area").value = USUARIO.area;
  }
  document.getElementById("form-error").innerHTML = "";
  document.getElementById("btn-aprobar").style.display = "none";
  document.getElementById("btn-rechazar").style.display = "none";
  document.getElementById("panel-servicios").style.display = "none";
}

async function cargarEnFormulario(id) {
  const d = CACHE_DEPS.find((x) => x.id === id);
  if (!d) return;
  document.getElementById("form-titulo").textContent = `Editar: ${d.nombre}`;
  document.getElementById("f-id").value = d.id;
  document.getElementById("f-nombre").value = d.nombre || "";
  document.getElementById("f-alias").value = (d.alias || []).join(", ");
  document.getElementById("f-tipo").value = d.tipo;
  document.getElementById("f-area").value = d.area || "";
  document.getElementById("f-categoria").value = d.categoria || "";
  document.getElementById("f-sede").value = d.sede_id || "";
  await cargarEdificios(d.sede_id);
  document.getElementById("f-edificio").value = d.edificio_id || "";
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

  document.getElementById("btn-aprobar").style.display = d.estado === "revision" && puedeAprobar(d) ? "" : "none";
  document.getElementById("btn-rechazar").style.display = d.estado === "activo" && puedeAprobar(d) ? "" : "none";

  document.getElementById("panel-servicios").style.display = "block";
  await cargarServicios(d.id);

  window.scrollTo({ top: document.getElementById("form-dep").offsetTop - 20, behavior: "smooth" });
}

document.getElementById("btn-cancelar").addEventListener("click", limpiarFormulario);

document.getElementById("btn-aprobar").addEventListener("click", async () => {
  const id = document.getElementById("f-id").value;
  if (!id) return;
  try {
    await api(`/admin/dependencias/${id}/aprobar`, { method: "POST" });
    limpiarFormulario();
    await Promise.all([cargarDependencias(), cargarStats()]);
  } catch (err) {
    document.getElementById("form-error").innerHTML = `<p class="error-msg">${err.message}</p>`;
  }
});

document.getElementById("btn-rechazar").addEventListener("click", async () => {
  const id = document.getElementById("f-id").value;
  if (!id) return;
  const comentario = prompt("Motivo (opcional) para devolver esto a revisión:") || "";
  try {
    await api(`/admin/dependencias/${id}/rechazar?comentario=${encodeURIComponent(comentario)}`, { method: "POST" });
    limpiarFormulario();
    await Promise.all([cargarDependencias(), cargarStats()]);
  } catch (err) {
    document.getElementById("form-error").innerHTML = `<p class="error-msg">${err.message}</p>`;
  }
});

document.getElementById("form-dep").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("f-id").value;
  const payload = {
    nombre: document.getElementById("f-nombre").value,
    alias: document.getElementById("f-alias").value,
    tipo: document.getElementById("f-tipo").value,
    area: document.getElementById("f-area").value,
    categoria: document.getElementById("f-categoria").value || null,
    sede_id: parseInt(document.getElementById("f-sede").value),
    edificio_id: document.getElementById("f-edificio").value ? parseInt(document.getElementById("f-edificio").value) : null,
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

// ── Servicios de la dependencia en edición ──
async function cargarServicios(depId) {
  const servicios = await api(`/admin/dependencias/${depId}/servicios`);
  const box = document.getElementById("lista-servicios");
  box.innerHTML = servicios.length
    ? ""
    : '<p class="hint" style="margin:0;">Todavía no hay servicios registrados.</p>';
  for (const s of servicios) {
    const row = document.createElement("div");
    row.className = "card";
    row.style.padding = "0.7rem 0.9rem";
    row.innerHTML = `
      <div class="card-top">
        <strong>${s.nombre}</strong>
        <button class="btn secondary" data-quitar-servicio="${s.id}" style="font-size:0.78rem; padding:0.25rem 0.6rem;">Quitar</button>
      </div>
      ${s.requisitos ? `<p class="meta">Requisitos: ${s.requisitos}</p>` : ""}
      ${s.canal ? `<p class="meta">Canal: ${s.canal}</p>` : ""}
    `;
    box.appendChild(row);
  }
  box.querySelectorAll("[data-quitar-servicio]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api(`/admin/servicios/${b.dataset.quitarServicio}`, { method: "DELETE" });
      await cargarServicios(depId);
    })
  );
}

document.getElementById("form-servicio").addEventListener("submit", async (e) => {
  e.preventDefault();
  const depId = document.getElementById("f-id").value;
  if (!depId) return;
  const payload = {
    nombre: document.getElementById("sv-nombre").value,
    requisitos: document.getElementById("sv-requisitos").value || null,
    canal: document.getElementById("sv-canal").value,
    estado: "activo",
  };
  await api(`/admin/dependencias/${depId}/servicios`, { method: "POST", body: JSON.stringify(payload) });
  document.getElementById("form-servicio").reset();
  await cargarServicios(depId);
});

// ── Auditoría ──
async function cargarAuditoria() {
  if (!puedeLeerAuditoria()) return;
  const registros = await api("/admin/auditoria");
  const tbody = document.querySelector("#tabla-auditoria tbody");
  tbody.innerHTML = "";
  for (const r of registros) {
    const tr = document.createElement("tr");
    const fecha = new Date(r.fecha).toLocaleString("es-PE");
    tr.innerHTML = `<td>${fecha}</td><td>${r.usuario_email || "—"}</td><td>${r.entidad || "—"}</td><td>${r.accion}</td><td>${r.detalle || ""}</td>`;
    tbody.appendChild(tr);
  }
}

async function cargarTodo() {
  await cargarSedes();
  limpiarFormulario();
  await Promise.all([cargarStats(), cargarDependencias(), cargarAuditoria(), cargarUsuarios()]);
}

iniciar();
