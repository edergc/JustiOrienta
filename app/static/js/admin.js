const API = "/api/v1";

// Los campos de DNI solo deben aceptar dígitos mientras se escribe -- el
// patrón HTML5 ya bloquea el envío del formulario, pero corregir la letra
// mal tecleada al vuelo es mejor experiencia que dejarla y recién avisar
// al enviar, sobre todo para personal no técnico.
document.querySelectorAll('input[pattern="[0-9]{8}"]').forEach((el) => {
  el.addEventListener("input", () => {
    el.value = el.value.replace(/\D/g, "").slice(0, 8);
  });
});

let TOKEN = sessionStorage.getItem("jo_token");
let USUARIO = null;
let CACHE_DEPS = [];
let CACHE_SEDES = [];
let CACHE_USUARIOS = [];

// El contenido del catálogo lo escribe cada área (texto libre, sin
// restricciones) -- cualquier innerHTML que lo interpole tiene que pasar por
// acá primero, o un nombre malicioso se ejecuta como HTML/JS en la sesión de
// quien lo vea (por ejemplo admin/auditor viendo "Posibles duplicados").
function escaparHtml(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

let toastTimer;
function mostrarToast(mensaje) {
  const el = document.getElementById("toast");
  el.textContent = mensaje;
  el.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("visible"), 2600);
}

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

// El QR se pide con fetch (no <a href> directo) porque el endpoint exige el
// token de sesión en el header Authorization -- un enlace normal del
// navegador no lo enviaría. Se abre en pestaña nueva para poder imprimirlo.
async function abrirQR(tipo, id) {
  try {
    const res = await fetch(`${API}/admin/qr/${tipo}/${id}`, { headers: headers(false) });
    if (!res.ok) throw new Error("No se pudo generar el código QR");
    const blob = await res.blob();
    window.open(URL.createObjectURL(blob), "_blank");
  } catch (err) {
    mostrarToast(err.message || "No se pudo generar el código QR");
  }
}

// Igual que abrirQR, pero forzando la descarga en vez de abrir una pestaña
// -- un .xlsx no se puede previsualizar en el navegador, así que necesita
// un enlace temporal con el atributo download en vez de window.open.
async function descargarArchivo(path, nombreSugerido, mensajeError) {
  try {
    const res = await fetch(`${API}${path}`, { headers: headers(false) });
    if (!res.ok) throw new Error(mensajeError);
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = nombreSugerido;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (err) {
    mostrarToast(err.message || mensajeError);
  }
}

function esAdmin() { return USUARIO && USUARIO.rol === "admin"; }
function puedeLeerAuditoria() { return USUARIO && (USUARIO.rol === "admin" || USUARIO.rol === "auditor"); }
function puedeVerReportes() {
  return USUARIO && (USUARIO.rol === "admin" || USUARIO.rol === "auditor" || USUARIO.rol === "consulta");
}
function esSoloConsulta() { return USUARIO && USUARIO.rol === "consulta"; }
function puedeAprobar(dep) {
  if (!USUARIO) return false;
  if (USUARIO.rol === "admin") return true;
  return USUARIO.rol === "validador" && USUARIO.area === dep.area;
}

function mostrarApp() {
  document.getElementById("vista-login").style.display = "none";
  document.getElementById("vista-app").style.display = "block";
  document.getElementById("perfil-nombre").textContent = USUARIO.nombre;
  document.getElementById("perfil-avatar").textContent = USUARIO.nombre ? USUARIO.nombre.trim()[0].toUpperCase() : "?";
  document.getElementById("perfil-dni").textContent = USUARIO.dni;
  document.getElementById("perfil-rol").textContent = USUARIO.rol;
  document.getElementById("perfil-area-fila").style.display = USUARIO.area ? "" : "none";
  document.getElementById("perfil-area").textContent = USUARIO.area || "";

  if (USUARIO.debe_cambiar_password) {
    // Nadie usa el resto del panel con una contraseña que eligió otra
    // persona -- el backend rechaza cualquier otro endpoint con 403 mientras
    // esto siga así, así que ni vale la pena pedir los datos de las pestañas.
    abrirModalPassword(true);
    return;
  }

  document.querySelector('[data-tab="tab-sedes"]').style.display = esAdmin() ? "" : "none";
  document.querySelector('[data-tab="tab-usuarios"]').style.display = esAdmin() ? "" : "none";
  document.querySelector('[data-tab="tab-auditoria"]').style.display = puedeLeerAuditoria() ? "" : "none";
  document.getElementById("fila-reporte").style.display = puedeVerReportes() ? "" : "none";

  // Siempre arrancar en "Dependencias": evita que quede activa una pestaña
  // que la sesión anterior dejó abierta y que este rol ya no puede ver.
  document.querySelectorAll(".tab-btn").forEach((b) => b.setAttribute("aria-pressed", "false"));
  document.querySelectorAll(".tab-panel").forEach((p) => (p.style.display = "none"));
  document.querySelector('[data-tab="tab-dependencias"]').setAttribute("aria-pressed", "true");

  // El rol "consulta" no gestiona el catálogo -- solo ve los indicadores de
  // arriba y descarga el reporte. Mostrarle las pestañas de edición (aunque
  // los botones fallaran con 403 al usarlos) sería confuso, no útil.
  document.getElementById("nav-tabs").style.display = esSoloConsulta() ? "none" : "";
  document.getElementById("panel-solo-consulta").style.display = esSoloConsulta() ? "block" : "none";
  if (!esSoloConsulta()) {
    document.getElementById("tab-dependencias").style.display = "block";
  }

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
  const dni = document.getElementById("login-dni").value;
  const pass = document.getElementById("login-pass").value;
  const body = new URLSearchParams();
  body.set("username", dni);
  body.set("password", pass);
  try {
    const res = await fetch(API + "/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "DNI o contraseña incorrectos" }));
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

// Salir del panel siempre cierra la sesión Y lleva al sitio público -- un
// solo camino para irse, en vez de un botón "Volver al inicio" aparte que
// dejaba el token vivo. En un equipo compartido (mostrador de atención), eso
// permitía que alguien más volviera a /admin ya autenticado con solo el
// botón "atrás", sin haber tecleado ninguna contraseña.
function salir() {
  cerrarSesion();
  window.location.href = "/";
}
document.getElementById("btn-logout").addEventListener("click", salir);
document.getElementById("link-marca-admin").addEventListener("click", salir);

// ── Menú "Mi perfil" ──
const btnPerfil = document.getElementById("btn-perfil");
const menuPerfil = document.getElementById("menu-perfil");
function cerrarMenuPerfil() {
  menuPerfil.style.display = "none";
  btnPerfil.setAttribute("aria-expanded", "false");
}
function alternarMenuPerfil() {
  const abierto = menuPerfil.style.display !== "none";
  menuPerfil.style.display = abierto ? "none" : "block";
  btnPerfil.setAttribute("aria-expanded", String(!abierto));
}
btnPerfil.addEventListener("click", (e) => {
  e.stopPropagation();
  alternarMenuPerfil();
});
// Clic afuera, o Escape, cierran el menú -- mismo patrón esperado que
// cualquier menú desplegable.
document.addEventListener("click", (e) => {
  if (!menuPerfil.contains(e.target) && e.target !== btnPerfil) cerrarMenuPerfil();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") cerrarMenuPerfil();
});
// Elegir cualquier acción del menú (cambiar contraseña o salir) lo cierra
// también, para no dejarlo abierto detrás del modal o de la pantalla de login.
document.getElementById("btn-mi-cuenta").addEventListener("click", cerrarMenuPerfil);
document.getElementById("btn-logout").addEventListener("click", cerrarMenuPerfil);

document.getElementById("btn-descargar-reporte").addEventListener("click", () => {
  const fecha = new Date().toISOString().slice(0, 10);
  descargarArchivo(
    "/admin/metricas/reporte.xlsx",
    `reporte_justicia_orienta_${fecha}.xlsx`,
    "No se pudo generar el reporte."
  );
});

document.getElementById("btn-exportar-catalogo").addEventListener("click", () => {
  const fecha = new Date().toISOString().slice(0, 10);
  descargarArchivo(
    "/admin/dependencias/exportar.xlsx",
    `catalogo_justicia_orienta_${fecha}.xlsx`,
    "No se pudo exportar el catálogo."
  );
});

// ── Mi contraseña ──
// obligatorio=true cuando debe_cambiar_password viene en true desde el
// backend (cuenta nueva o restablecida por admin) -- mientras dura, no se
// puede cancelar ni cerrar con Escape: es justo lo que el servidor también
// exige (403 en cualquier otro endpoint), así que dejar "cancelar" visible
// solo confundiría sin lograr nada.
let passwordObligatorio = false;

function abrirModalPassword(obligatorio = false) {
  passwordObligatorio = obligatorio;
  document.getElementById("form-password").reset();
  document.getElementById("form-password-error").innerHTML = "";
  document.getElementById("modal-password-titulo").textContent = obligatorio
    ? "Debes elegir una nueva contraseña para continuar"
    : "Cambiar mi contraseña";
  document.getElementById("modal-password-motivo").style.display = obligatorio ? "block" : "none";
  document.getElementById("btn-password-cancelar").style.display = obligatorio ? "none" : "";
  document.getElementById("modal-password").style.display = "flex";
  document.getElementById("p-actual").focus();
}
function cerrarModalPassword() {
  if (passwordObligatorio) return;
  document.getElementById("modal-password").style.display = "none";
  // Devuelve el foco a quien abrió el modal -- sin esto, alguien navegando
  // solo con teclado queda "perdido" en el body tras cerrar.
  document.getElementById("btn-mi-cuenta").focus();
}
document.getElementById("btn-mi-cuenta").addEventListener("click", () => abrirModalPassword(false));
document.getElementById("btn-password-cancelar").addEventListener("click", cerrarModalPassword);
document.getElementById("form-password").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/auth/mi-password", {
      method: "PUT",
      body: JSON.stringify({
        password_actual: document.getElementById("p-actual").value,
        password_nueva: document.getElementById("p-nueva").value,
      }),
    });
    USUARIO.debe_cambiar_password = false;
    const eraObligatorio = passwordObligatorio;
    passwordObligatorio = false;
    document.getElementById("btn-password-cancelar").style.display = "";
    cerrarModalPassword(); // ya no es obligatorio: cierra normal y devuelve el foco
    mostrarToast("Contraseña actualizada.");
    if (eraObligatorio) mostrarApp(); // recién ahora carga las pestañas y sus datos
  } catch (err) {
    document.getElementById("form-password-error").innerHTML = `<p class="error-msg">${err.message}</p>`;
  }
});
// Escape cierra el modal, y Tab no debe poder escaparse de él mientras está
// abierto -- si no, alguien navegando solo con teclado termina detrás del
// fondo oscurecido que visualmente tapa el resto de la página.
document.getElementById("modal-password").addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    cerrarModalPassword();
    return;
  }
  if (e.key !== "Tab") return;
  // offsetParent === null excluye el botón "Cancelar" cuando el cambio es
  // obligatorio y queda oculto -- si no, el trampolín de Tab intenta
  // enfocar un elemento invisible y el foco se escapa del modal.
  const enfocables = [...document.querySelectorAll("#modal-password button, #modal-password input")].filter(
    (el) => el.offsetParent !== null
  );
  const primero = enfocables[0];
  const ultimo = enfocables[enfocables.length - 1];
  if (e.shiftKey && document.activeElement === primero) {
    e.preventDefault();
    ultimo.focus();
  } else if (!e.shiftKey && document.activeElement === ultimo) {
    e.preventDefault();
    primero.focus();
  }
});

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
  const porcentaje = (v) => (v !== null && v !== undefined ? v + "%" : "—");
  const items = [
    [s.total_consultas, "Consultas totales"],
    [s.consultas_resueltas, "Resueltas"],
    [s.consultas_sin_resultado, "Sin resultado"],
    [porcentaje(s.porcentaje_resueltas), "% de acierto"],
    [porcentaje(s.porcentaje_satisfaccion), "% satisfacción (de quienes respondieron)"],
    [porcentaje(s.porcentaje_modo_accesible), "% en modo accesible"],
    [porcentaje(s.porcentaje_via_voz), "% por voz"],
    [porcentaje(s.porcentaje_sobre_accesibilidad), "% sobre accesibilidad"],
  ];
  // Gestor/validador tienen un área propia -- en vez de obligarlos a leer la
  // lista agregada de "Pendientes por área" (con las de todas las áreas),
  // se les resalta de una vez cuántos pendientes tiene SU área, en rojo si
  // hay algo esperando.
  if (USUARIO && USUARIO.area) {
    const propia = s.pendientes_por_area.find((p) => p.area === USUARIO.area);
    const cantidad = propia ? propia.cantidad : 0;
    const detalle = propia ? ` (~${propia.antiguedad_promedio_dias} días en promedio)` : "";
    items.push([cantidad, `Pendientes en tu área${detalle}`, cantidad > 0]);
  }
  for (const [n, l, alerta] of items) {
    const d = document.createElement("div");
    d.className = "stat";
    d.innerHTML = `<div class="n"${alerta ? ' style="color:var(--danger)"' : ""}>${n}</div><div class="l">${l}</div>`;
    box.appendChild(d);
  }

  const listaTop = document.getElementById("lista-top-consultas");
  listaTop.innerHTML = s.top_consultas.length
    ? s.top_consultas.map((t) => `<li>${t.consulta} <span class="hint">(${t.veces})</span></li>`).join("")
    : '<li class="hint" style="list-style:none;">Todavía no hay datos.</li>';

  const listaVacia = '<li class="hint" style="list-style:none;">Todavía no hay datos.</li>';

  const listaSede = document.getElementById("lista-consultas-sede");
  listaSede.innerHTML = s.consultas_por_sede.length
    ? s.consultas_por_sede.map((c) => `<li>${c.sede} <span class="hint">(${c.veces})</span></li>`).join("")
    : listaVacia;

  const listaArea = document.getElementById("lista-consultas-area");
  listaArea.innerHTML = s.consultas_por_area.length
    ? s.consultas_por_area.map((c) => `<li>${c.area} <span class="hint">(${c.veces})</span></li>`).join("")
    : listaVacia;

  const TIPO_LABEL = { jurisdiccional: "Jurisdiccional", administrativa: "Administrativa", servicio: "Servicio" };
  const listaTipo = document.getElementById("lista-consultas-tipo");
  listaTipo.innerHTML = s.consultas_por_tipo.length
    ? s.consultas_por_tipo.map((c) => `<li>${TIPO_LABEL[c.tipo] || c.tipo} <span class="hint">(${c.veces})</span></li>`).join("")
    : listaVacia;

  const listaSinResultado = document.getElementById("lista-top-sin-resultado");
  listaSinResultado.innerHTML = s.top_consultas_sin_resultado.length
    ? s.top_consultas_sin_resultado.map((t) => `<li>${t.consulta} <span class="hint">(${t.veces})</span></li>`).join("")
    : '<li class="hint" style="list-style:none;">Sin búsquedas sin resultado todavía -- buena señal.</li>';

  const listaPendientes = document.getElementById("lista-pendientes-area");
  listaPendientes.innerHTML = s.pendientes_por_area.length
    ? s.pendientes_por_area
        .map((p) => `<li>${p.area} <span class="hint">(${p.cantidad}, ${p.antiguedad_promedio_dias} días en promedio)</span></li>`)
        .join("")
    : '<li class="hint" style="list-style:none;">No hay nada pendiente de aprobar en este momento.</li>';
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
      <td>
        ${esAdmin() ? `<button class="btn secondary" data-editar-sede="${s.id}">Editar</button>` : ""}
        <button class="btn secondary" data-qr-sede="${s.id}">QR</button>
      </td>`;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll("[data-editar-sede]").forEach((b) =>
    b.addEventListener("click", () => cargarSedeEnFormulario(parseInt(b.dataset.editarSede)))
  );
  tbody.querySelectorAll("[data-qr-sede]").forEach((b) =>
    b.addEventListener("click", () => abrirQR("sede", parseInt(b.dataset.qrSede)))
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
  document.getElementById("s-estado").value = s.estado || "activo";
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
    estado: document.getElementById("s-estado").value,
  };
  try {
    if (id) await api(`/admin/sedes/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    else await api("/admin/sedes", { method: "POST", body: JSON.stringify(payload) });
    limpiarFormularioSede();
    await cargarSedes();
    mostrarToast("Sede guardada.");
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
  CACHE_USUARIOS = await api("/admin/usuarios");
  const tbody = document.querySelector("#tabla-usuarios tbody");
  tbody.innerHTML = "";
  for (const u of CACHE_USUARIOS) {
    const tr = document.createElement("tr");
    const ultimo = u.ultimo_acceso ? new Date(u.ultimo_acceso).toLocaleString("es-PE") : "Nunca";
    // Bloqueo automático tras intentos fallidos (ver app/crud/usuarios.py):
    // se muestra aparte de Activo/Inactivo porque es temporal y se levanta
    // solo con guardar la ficha desde "Editar", no con un interruptor propio.
    const bloqueado = u.bloqueado_hasta && new Date(u.bloqueado_hasta) > new Date();
    const badgeBloqueo = bloqueado
      ? ` <span class="badge inactivo" title="Se levanta al guardar la ficha, o solo(a) al pasar la hora indicada">Bloqueada hasta ${new Date(u.bloqueado_hasta).toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" })}</span>`
      : "";
    tr.innerHTML = `
      <td>${u.nombre}</td><td>${u.dni}</td><td>${u.rol}</td><td>${u.area || "—"}</td>
      <td>${u.activo ? '<span class="badge activo">Activo</span>' : '<span class="badge inactivo">Inactivo</span>'}${badgeBloqueo}</td>
      <td>${ultimo}</td>
      <td><button class="btn secondary" data-editar-usuario="${u.id}">Editar</button></td>`;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll("[data-editar-usuario]").forEach((b) =>
    b.addEventListener("click", () => cargarUsuarioEnFormulario(parseInt(b.dataset.editarUsuario)))
  );
}

function limpiarFormularioUsuario() {
  document.getElementById("form-usuario-titulo").textContent = "Nuevo usuario";
  document.getElementById("u-id").value = "";
  document.getElementById("form-usuario").reset();
  document.getElementById("form-usuario-error").innerHTML = "";
  document.getElementById("campo-u-dni").style.display = "";
  document.getElementById("u-dni").required = true;
  document.getElementById("u-password").required = true;
  document.getElementById("u-password").placeholder = "";
  document.querySelector('#campo-u-password label').textContent = "Contraseña inicial *";
  document.getElementById("campo-u-activo").style.display = "none";
  document.getElementById("btn-usuario-guardar").textContent = "Crear usuario";
  document.getElementById("btn-usuario-cancelar").style.display = "none";
}

function cargarUsuarioEnFormulario(id) {
  const u = CACHE_USUARIOS.find((x) => x.id === id);
  if (!u) return;
  document.getElementById("form-usuario-titulo").textContent = `Editar: ${u.nombre}`;
  document.getElementById("u-id").value = u.id;
  document.getElementById("u-nombre").value = u.nombre;
  document.getElementById("u-rol").value = u.rol;
  document.getElementById("u-area").value = u.area || "";
  document.getElementById("u-activo").checked = u.activo;

  // El DNI es el identificador de acceso: no se edita aquí.
  document.getElementById("campo-u-dni").style.display = "none";
  document.getElementById("u-dni").required = false;
  document.getElementById("u-password").value = "";
  document.getElementById("u-password").required = false;
  document.getElementById("u-password").placeholder = "Dejar en blanco para no cambiarla";
  document.querySelector('#campo-u-password label').textContent = "Nueva contraseña (opcional)";
  document.getElementById("campo-u-activo").style.display = "";
  document.getElementById("btn-usuario-guardar").textContent = "Guardar cambios";
  document.getElementById("btn-usuario-cancelar").style.display = "";

  window.scrollTo({ top: document.getElementById("form-usuario").offsetTop - 20, behavior: "smooth" });
}

document.getElementById("btn-usuario-cancelar").addEventListener("click", limpiarFormularioUsuario);

document.getElementById("form-usuario").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("u-id").value;
  try {
    if (id) {
      const payload = {
        nombre: document.getElementById("u-nombre").value,
        rol: document.getElementById("u-rol").value,
        area: document.getElementById("u-area").value || null,
        activo: document.getElementById("u-activo").checked,
        nueva_password: document.getElementById("u-password").value || null,
      };
      await api(`/admin/usuarios/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    } else {
      const payload = {
        nombre: document.getElementById("u-nombre").value,
        dni: document.getElementById("u-dni").value,
        password: document.getElementById("u-password").value,
        rol: document.getElementById("u-rol").value,
        area: document.getElementById("u-area").value || null,
      };
      await api("/admin/usuarios", { method: "POST", body: JSON.stringify(payload) });
    }
    limpiarFormularioUsuario();
    await cargarUsuarios();
    mostrarToast("Usuario guardado.");
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

const DEP_LIMITE = 10;
let depSkip = 0;

async function cargarDependencias() {
  const estado = document.getElementById("filtro-estado").value;
  const q = document.getElementById("filtro-nombre").value.trim();
  const params = new URLSearchParams({ skip: depSkip, limite: DEP_LIMITE });
  if (estado) params.set("estado", estado);
  if (q) params.set("q", q);

  const resp = await api(`/admin/dependencias?${params}`);
  CACHE_DEPS = resp.items;

  const tbody = document.querySelector("#tabla-dependencias tbody");
  tbody.innerHTML = CACHE_DEPS.length
    ? ""
    : '<tr><td colspan="5" class="hint" style="padding:1rem;">Sin resultados.</td></tr>';
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
        <button class="btn secondary" data-qr="${d.id}">QR</button>
        <button class="btn secondary" data-desactivar="${d.id}">Desactivar</button>
      </td>`;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll("[data-editar]").forEach((b) =>
    b.addEventListener("click", () => cargarEnFormulario(parseInt(b.dataset.editar)))
  );
  tbody.querySelectorAll("[data-qr]").forEach((b) =>
    b.addEventListener("click", () => abrirQR("dependencia", parseInt(b.dataset.qr)))
  );
  tbody.querySelectorAll("[data-desactivar]").forEach((b) =>
    b.addEventListener("click", () => desactivar(parseInt(b.dataset.desactivar)))
  );

  renderPaginacionDep(resp.total);
}

function renderPaginacionDep(total) {
  const box = document.getElementById("paginacion-dep");
  if (total === 0) {
    box.innerHTML = "";
    return;
  }
  const desde = depSkip + 1;
  const hasta = Math.min(depSkip + DEP_LIMITE, total);
  box.innerHTML = `
    <span>Mostrando ${desde}–${hasta} de ${total}</span>
    <div style="display:flex; gap:0.5rem;">
      <button class="btn secondary" id="btn-dep-anterior" ${depSkip === 0 ? "disabled" : ""}>← Anterior</button>
      <button class="btn secondary" id="btn-dep-siguiente" ${hasta >= total ? "disabled" : ""}>Siguiente →</button>
    </div>`;
  document.getElementById("btn-dep-anterior").addEventListener("click", () => {
    depSkip = Math.max(0, depSkip - DEP_LIMITE);
    cargarDependencias();
  });
  document.getElementById("btn-dep-siguiente").addEventListener("click", () => {
    depSkip += DEP_LIMITE;
    cargarDependencias();
  });
}

function reiniciarYCargarDependencias() {
  depSkip = 0;
  cargarDependencias();
}
document.getElementById("filtro-estado").addEventListener("change", reiniciarYCargarDependencias);
let filtroNombreDebounce;
document.getElementById("filtro-nombre").addEventListener("input", () => {
  clearTimeout(filtroNombreDebounce);
  filtroNombreDebounce = setTimeout(reiniciarYCargarDependencias, 300);
});

async function desactivar(id) {
  if (!confirm("¿Desactivar esta dependencia? Dejará de verse en el sitio público.")) return;
  await api(`/admin/dependencias/${id}`, { method: "DELETE" });
  await Promise.all([cargarDependencias(), cargarStats()]);
  mostrarToast("Dependencia desactivada.");
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
  document.getElementById("f-instrucciones").value = d.instrucciones_internas || "";
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
    mostrarToast("Publicado. Ya es visible en el sitio público.");
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
    mostrarToast("Devuelto a revisión.");
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
    instrucciones_internas: document.getElementById("f-instrucciones").value || null,
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
    mostrarToast("Dependencia guardada.");
  } catch (err) {
    document.getElementById("form-error").innerHTML = `<p class="error-msg">${err.message}</p>`;
  }
});

// ── Servicios de la dependencia en edición ──
async function cargarServicios(depId) {
  // incluir_inactivos=true: si no, un servicio "Quitado" desaparece para
  // siempre de esta lista -- sin forma de verlo de nuevo ni reactivarlo salvo
  // tocando la base de datos a mano (el mismo bug que ya se corrigió para
  // sedes con el selector de Estado real).
  const servicios = await api(`/admin/dependencias/${depId}/servicios?incluir_inactivos=true`);
  const box = document.getElementById("lista-servicios");
  box.innerHTML = servicios.length
    ? ""
    : '<p class="hint" style="margin:0;">Todavía no hay servicios registrados.</p>';
  for (const s of servicios) {
    const inactivo = s.estado !== "activo";
    const row = document.createElement("div");
    row.className = "card";
    row.style.padding = "0.7rem 0.9rem";
    if (inactivo) row.style.opacity = "0.6";
    row.innerHTML = `
      <div class="card-top">
        <strong>${s.nombre}</strong>${inactivo ? ' <span class="badge inactivo">Inactivo</span>' : ""}
        ${
          inactivo
            ? `<button class="btn secondary" data-reactivar-servicio="${s.id}" style="font-size:0.78rem; padding:0.25rem 0.6rem;">Reactivar</button>`
            : `<button class="btn secondary" data-quitar-servicio="${s.id}" style="font-size:0.78rem; padding:0.25rem 0.6rem;">Quitar</button>`
        }
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
  box.querySelectorAll("[data-reactivar-servicio]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api(`/admin/servicios/${b.dataset.reactivarServicio}/reactivar`, { method: "POST" });
      await cargarServicios(depId);
      mostrarToast("Servicio reactivado.");
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
    tr.innerHTML = `<td>${fecha}</td><td>${r.usuario_dni || "—"}</td><td>${r.entidad || "—"}</td><td>${r.accion}</td><td>${r.detalle || ""}</td>`;
    tbody.appendChild(tr);
  }
  await cargarDuplicados();
}

async function cargarDuplicados() {
  const box = document.getElementById("lista-duplicados");
  const grupos = await api("/admin/dependencias/duplicados");
  if (!grupos.length) {
    box.innerHTML = '<p class="hint" style="margin:0;">No se encontraron nombres repetidos dentro de la misma sede.</p>';
    return;
  }
  box.innerHTML = grupos
    .map((g) => {
      const filas = g.dependencias
        .map(
          (d) =>
            `<li>#${d.id} -- ${escaparHtml(d.area)}${d.piso ? `, piso ${escaparHtml(d.piso)}` : ""}${d.oficina ? `, oficina ${escaparHtml(d.oficina)}` : ""}` +
            // d.estado viene de un campo restringido del servidor (Literal), no de texto libre -- no hace falta escaparlo
            ` <span class="badge ${d.estado}">${d.estado}</span></li>`
        )
        .join("");
      return `
        <div class="card" style="padding:0.8rem 1rem; margin-bottom:0.6rem;">
          <strong>"${escaparHtml(g.nombre)}"</strong> <span class="hint">-- ${escaparHtml(g.sede)} (${g.dependencias.length} veces)</span>
          <ul class="meta" style="padding-left:1.2rem; margin:0.4rem 0 0;">${filas}</ul>
        </div>`;
    })
    .join("");
}

async function cargarTodo() {
  // El rol "consulta" no ve ninguna de las pestañas de gestión del catálogo
  // (ver mostrarApp) y el backend ahora rechaza /admin/dependencias para ese
  // rol -- pedir estos datos igual sería un viaje de red desperdiciado, y en
  // el caso de dependencias, un error 403 innecesario en la consola.
  if (esSoloConsulta()) {
    await cargarStats();
    return;
  }
  await cargarSedes();
  limpiarFormulario();
  limpiarFormularioUsuario();
  depSkip = 0;
  document.getElementById("filtro-nombre").value = "";
  await Promise.all([cargarStats(), cargarDependencias(), cargarAuditoria(), cargarUsuarios()]);
}

iniciar();
