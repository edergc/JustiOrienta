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

// El backend guarda y serializa datetimes en UTC pero sin indicarlo (sin
// "Z" ni offset) -- "2026-08-26T21:58:00", no "...Z". `new Date(...)` de
// JavaScript interpreta un string asi como HORA LOCAL del navegador, no
// UTC: en Lima (UTC-5) eso corre cada fecha del servidor 5 horas hacia
// adelante, y algo recien actualizado aparece "en el futuro" (por ejemplo,
// el semaforo de vigencia mostrando "-1 dias"). Esta funcion fuerza la
// interpretacion correcta agregando "Z" solo si el string todavia no trae
// zona horaria.
function fechaServidor(iso) {
  if (!iso) return null;
  const conZona = /Z$|[+-]\d\d:\d\d$/.test(iso);
  return new Date(conZona ? iso : iso + "Z");
}

// ── Modales genéricos (crear/editar dependencia, sede, usuario) ──
// Mismo patrón de accesibilidad que ya usaba el modal de contraseña (Escape
// cierra, Tab no se escapa, clic en el fondo oscurecido también cierra),
// reutilizable para no triplicar la misma lógica en los tres formularios.
const _focoPrevioModal = {};
function abrirModal(modalId, elementoAFocar) {
  _focoPrevioModal[modalId] = document.activeElement;
  const modal = document.getElementById(modalId);
  modal.style.display = "flex";
  (elementoAFocar || modal.querySelector("input, select, textarea")).focus();
}
function cerrarModal(modalId, focoAlternativo) {
  document.getElementById(modalId).style.display = "none";
  const previo = _focoPrevioModal[modalId];
  if (previo && document.body.contains(previo)) previo.focus();
  else if (focoAlternativo) focoAlternativo.focus();
}
function configurarCierreModal(modalId, alCerrar) {
  const modal = document.getElementById(modalId);
  modal.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { alCerrar(); return; }
    if (e.key !== "Tab") return;
    const enfocables = [...modal.querySelectorAll("button, input, select, textarea")].filter(
      (el) => el.offsetParent !== null && !el.disabled
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
  modal.addEventListener("click", (e) => {
    if (e.target === modal) alCerrar();
  });
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

// Trazabilidad de la orientacion en una sola vista: quien publico el dato
// vigente (auditoria) y cuanto se uso como respuesta a un ciudadano
// (consultas) -- responde "por que el sistema mostro esto" sin cruzar dos
// tablas a mano.
async function abrirHistorial(depId) {
  const cont = document.getElementById("historial-contenido");
  cont.innerHTML = '<p class="hint">Cargando…</p>';
  abrirModal("modal-historial", document.getElementById("btn-historial-cerrar"));
  try {
    const h = await api(`/admin/dependencias/${depId}/historial`);
    const fecha = (f) => (f ? fechaServidor(f).toLocaleString("es-PE") : "Nunca");
    const cambios = h.cambios.length
      ? h.cambios
          .map(
            (c) =>
              `<li><strong>${escaparHtml(c.accion)}</strong> por ${escaparHtml(c.usuario_dni || "sistema")} -- ${fecha(c.fecha)}<br><span class="hint">${escaparHtml(c.detalle || "")}</span></li>`
          )
          .join("")
      : '<li class="hint" style="list-style:none;">Sin cambios registrados individualmente (posiblemente cargado por script masivo).</li>';
    cont.innerHTML = `
      <p class="meta"><strong>${escaparHtml(h.nombre)}</strong> -- ${estadoBadge(h.estado)}</p>
      <p class="meta">Ultima actualizacion de contenido: ${fecha(h.actualizado_en)}</p>
      <p class="meta">Mostrada como respuesta a un ciudadano: <strong>${h.veces_mostrada_como_respuesta}</strong> ${h.veces_mostrada_como_respuesta === 1 ? "vez" : "veces"}${h.ultima_vez_mostrada ? " -- la ultima el " + fecha(h.ultima_vez_mostrada) : ""}</p>
      <p class="meta" style="margin-top:0.8rem;"><strong>Historial de cambios:</strong></p>
      <ul style="padding-left:1.1rem; max-height:16rem; overflow-y:auto;">${cambios}</ul>
    `;
  } catch (err) {
    cont.innerHTML = `<p class="error-msg">${escaparHtml(err.message || "No se pudo cargar el historial")}</p>`;
  }
}
document.getElementById("btn-historial-cerrar").addEventListener("click", () =>
  cerrarModal("modal-historial")
);
configurarCierreModal("modal-historial", () => cerrarModal("modal-historial"));

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
function puedeLeerAuditoria() {
  return USUARIO && (USUARIO.rol === "admin" || USUARIO.rol === "auditor" || USUARIO.rol === "consulta");
}
function puedeVerReportes() {
  return USUARIO && (USUARIO.rol === "admin" || USUARIO.rol === "auditor" || USUARIO.rol === "consulta");
}
function esSoloConsulta() { return USUARIO && USUARIO.rol === "consulta"; }

const TITULOS_TAB = {
  "tab-dashboard": "Dashboard",
  "tab-dependencias": "Dependencias",
  "tab-sedes": "Sedes",
  "tab-mapa": "Mapa interno",
  "tab-usuarios": "Usuarios",
  "tab-auditoria": "Auditoría",
};
function actualizarTituloTopbar(tabId) {
  document.getElementById("admin-topbar-titulo").textContent = TITULOS_TAB[tabId] || "Panel de administración";
}
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

  // La visibilidad por rol se aplica ANTES de mirar debe_cambiar_password:
  // si no, alguien con una cuenta nueva veía (atenuadas detrás del modal
  // obligatorio, pero visibles) las pestañas de gestión que su rol nunca
  // debería mostrar -- por ejemplo, "consulta" alcanzaba a ver "Dependencias"
  // y "+ Nueva dependencia" un instante antes de elegir su contraseña.
  //
  // "consulta" no gestiona el catálogo (nunca ve "Dependencias"), pero sí
  // supervisa: lee auditoría y el detector de duplicados en solo lectura,
  // mismo alcance que auditor para esa única pestaña.
  document.querySelector('[data-tab="tab-dependencias"]').style.display = esSoloConsulta() ? "none" : "";
  document.querySelector('[data-tab="tab-sedes"]').style.display = esAdmin() ? "" : "none";
  document.querySelector('[data-tab="tab-usuarios"]').style.display = esAdmin() ? "" : "none";
  document.querySelector('[data-tab="tab-auditoria"]').style.display = puedeLeerAuditoria() ? "" : "none";
  document.querySelector('[data-tab="tab-mapa"]').style.display = esAdmin() ? "" : "none";
  document.getElementById("fila-reporte").style.display = puedeVerReportes() ? "" : "none";
  document.getElementById("panel-titulares").style.display = esAdmin() ? "" : "none";

  // Las etiquetas de grupo del menú ("Catálogo", "Control") solo tienen
  // sentido si algún botón del grupo quedó visible para este rol -- si no,
  // quedaría un título de sección flotando sin nada debajo.
  document.querySelectorAll(".admin-nav-grupo").forEach((etiqueta) => {
    let hayVisible = false;
    for (let el = etiqueta.nextElementSibling; el && !el.classList.contains("admin-nav-grupo"); el = el.nextElementSibling) {
      if (el.classList.contains("tab-btn") && el.style.display !== "none") hayVisible = true;
    }
    etiqueta.style.display = hayVisible ? "" : "none";
  });

  document.querySelectorAll(".tab-btn").forEach((b) => b.setAttribute("aria-pressed", "false"));
  document.querySelectorAll(".tab-panel").forEach((p) => (p.style.display = "none"));

  // El Dashboard es la pantalla de entrada para cualquier rol -- ahí se ven
  // los indicadores (incluido "consulta", que no gestiona catálogo) y desde
  // ahí cada quien elige a qué sección ir.
  const tabInicial = "tab-dashboard";
  document.querySelector(`[data-tab="${tabInicial}"]`).setAttribute("aria-pressed", "true");
  document.getElementById(tabInicial).style.display = "block";
  actualizarTituloTopbar(tabInicial);

  document.getElementById("panel-solo-consulta").style.display = esSoloConsulta() ? "block" : "none";
  const hayPestañaVisible = [...document.querySelectorAll(".tab-btn")].some((b) => b.style.display !== "none");
  document.getElementById("nav-tabs").style.display = hayPestañaVisible ? "" : "none";

  if (USUARIO.debe_cambiar_password) {
    // Nadie usa el resto del panel con una contraseña que eligió otra
    // persona -- el backend rechaza cualquier otro endpoint con 403 mientras
    // esto siga así, así que ni vale la pena pedir los datos de las pestañas.
    abrirModalPassword(true);
    return;
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

// Si el enlace del correo de "olvidé mi contraseña" trae ?reset=token, se
// muestra el formulario para elegir la nueva contraseña en vez del login
// -- sin esto, quien hace clic en el enlace no tendría dónde escribirla.
function tokenDeRestablecerEnURL() {
  return new URLSearchParams(window.location.search).get("reset");
}

async function iniciar() {
  const tokenReset = tokenDeRestablecerEnURL();
  if (tokenReset) {
    document.getElementById("r-token").value = tokenReset;
    document.getElementById("login-box-login").style.display = "none";
    document.getElementById("login-box-restablecer").style.display = "block";
    return mostrarLogin();
  }
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

// ── "¿Olvidaste tu contraseña?" ──
document.getElementById("btn-abrir-olvide").addEventListener("click", () => {
  document.getElementById("form-olvide").reset();
  document.getElementById("olvide-error").innerHTML = "";
  document.getElementById("olvide-exito").style.display = "none";
  document.getElementById("form-olvide").style.display = "";
  abrirModal("modal-olvide", document.getElementById("olvide-dni"));
});
document.getElementById("btn-olvide-cancelar").addEventListener("click", () => cerrarModal("modal-olvide", document.getElementById("btn-abrir-olvide")));
configurarCierreModal("modal-olvide", () => cerrarModal("modal-olvide", document.getElementById("btn-abrir-olvide")));

document.getElementById("form-olvide").addEventListener("submit", async (e) => {
  e.preventDefault();
  const dni = document.getElementById("olvide-dni").value;
  const errorBox = document.getElementById("olvide-error");
  errorBox.innerHTML = "";
  try {
    const data = await api("/auth/olvide-password", { method: "POST", body: JSON.stringify({ dni }) });
    document.getElementById("olvide-exito").innerHTML =
      `<p class="meta" style="color:var(--accent2-strong); font-weight:600;">✓ ${data.mensaje}</p>` +
      `<button class="btn secondary" type="button" id="btn-olvide-cerrar-exito" style="margin-top:0.6rem;">Cerrar</button>`;
    document.getElementById("olvide-exito").style.display = "";
    document.getElementById("form-olvide").style.display = "none";
    document.getElementById("btn-olvide-cerrar-exito").addEventListener("click", () =>
      cerrarModal("modal-olvide", document.getElementById("btn-abrir-olvide"))
    );
  } catch (err) {
    errorBox.innerHTML = `<p class="error-msg">${err.message}</p>`;
  }
});

// ── Elegir nueva contraseña desde el enlace del correo ──
document.getElementById("form-restablecer").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorBox = document.getElementById("restablecer-error");
  errorBox.innerHTML = "";
  const nueva = document.getElementById("r-nueva").value;
  const confirmar = document.getElementById("r-confirmar").value;
  if (nueva !== confirmar) {
    errorBox.innerHTML = `<p class="error-msg">Las contraseñas no coinciden.</p>`;
    return;
  }
  try {
    await api("/auth/restablecer-password", {
      method: "POST",
      body: JSON.stringify({ token: document.getElementById("r-token").value, nueva_password: nueva }),
    });
    window.history.replaceState({}, "", "/admin");
    document.getElementById("login-box-restablecer").style.display = "none";
    document.getElementById("login-box-login").style.display = "";
    mostrarLogin();
    document.getElementById("login-error").innerHTML =
      '<p class="meta" style="color:var(--accent2-strong); font-weight:600;">✓ Contraseña actualizada. Ya puedes iniciar sesión.</p>';
  } catch (err) {
    errorBox.innerHTML = `<p class="error-msg">${err.message}</p>`;
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

// ── Actualizar titulares desde el reporte de Conformación ──
document.getElementById("form-titulares").addEventListener("submit", async (e) => {
  e.preventDefault();
  const archivo = document.getElementById("t-archivo").files[0];
  const sede = document.getElementById("t-sede").value;
  const caja = document.getElementById("resultado-titulares");
  if (!archivo) return;

  const boton = document.getElementById("btn-titulares-enviar");
  boton.disabled = true;
  boton.textContent = "Procesando…";
  caja.innerHTML = "";

  const datos = new FormData();
  datos.append("archivo", archivo);
  if (sede) datos.append("sede", sede);

  try {
    const resumen = await api("/admin/dependencias/importar-titulares", {
      method: "POST",
      body: datos,
      jsonBody: false,
    });
    const pendientes = resumen.sin_emparejar || [];
    caja.innerHTML = `
      <p><strong>${resumen.actualizadas}</strong> dependencias actualizadas con titular.
      ${resumen.ya_tenian} ya tenían titular (no se tocaron).
      ${pendientes.length} sin emparejar en el catálogo.</p>
      ${pendientes.length ? `
        <details>
          <summary>Ver las ${pendientes.length} sin emparejar</summary>
          <ul style="margin-top:0.5rem;">${pendientes.map((p) => `<li>${escaparHtml(p)}</li>`).join("")}</ul>
        </details>` : ""}
    `;
    document.getElementById("form-titulares").reset();
    document.getElementById("t-sede").value = sede;
    mostrarToast("Titulares actualizados.");
  } catch (err) {
    caja.innerHTML = `<p class="error-msg">${escaparHtml(err.message)}</p>`;
  } finally {
    boton.disabled = false;
    boton.textContent = "Actualizar titulares";
  }
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
    actualizarTituloTopbar(btn.dataset.tab);
    window.scrollTo({ top: 0, behavior: "instant" });
  });
});

// ── Estadísticas ──
async function cargarStats() {
  const s = await api("/admin/metricas/resumen");
  const box = document.getElementById("stats");
  box.innerHTML = "";
  const porcentaje = (v) => (v !== null && v !== undefined ? v + "%" : "—");
  const items = [
    [porcentaje(s.primera_orientacion_correcta), "Primera orientación correcta (meta: >80%)"],
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
  items.forEach(([n, l, alerta], indice) => {
    const d = document.createElement("div");
    // El primer indicador es la meta declarada del proyecto (primera
    // orientación correcta, >80%) -- se destaca como "hero" con una barra
    // de progreso, en vez de quedar igual de chico que el resto.
    const esHero = indice === 0 && typeof s.primera_orientacion_correcta === "number";
    d.className = "stat" + (esHero ? " stat-hero" : "");
    const numeroYEtiqueta = `<div class="n"${alerta ? ' style="color:var(--danger)"' : ""}>${n}</div><div class="l">${l}</div>`;
    if (esHero) {
      const pct = Math.max(0, Math.min(100, s.primera_orientacion_correcta));
      d.innerHTML =
        `<div class="stat-hero-texto">${numeroYEtiqueta}</div>` +
        `<div class="stat-hero-texto"><div class="stat-barra"><i style="width:${pct}%"></i></div>` +
        `<div class="stat-meta">Meta institucional: 80%</div></div>`;
    } else {
      d.innerHTML = numeroYEtiqueta;
    }
    box.appendChild(d);
  });

  // Cada fila lleva una mini-barra proporcional al valor más alto de su
  // propia lista -- convierte los rankings de texto plano en algo que se
  // lee de un vistazo, sin sacar una librería de gráficos para esto.
  const filaConBarra = (etiquetaHtml, valor, max) => {
    const pct = max > 0 ? Math.max(4, Math.round((valor / max) * 100)) : 0;
    return `<li><div class="fila-texto">${etiquetaHtml}</div><div class="mini-barra"><i style="width:${pct}%"></i></div></li>`;
  };
  const maxDe = (arr, campo) => Math.max(1, ...arr.map((x) => x[campo]));
  const listaVacia = '<li class="hint" style="list-style:none;">Todavía no hay datos.</li>';

  // t.consulta es el texto que alguien escribió en el buscador PÚBLICO, sin
  // ninguna cuenta ni restricción -- escaparHtml() es obligatorio acá, no
  // opcional: sin esto, cualquier persona anónima podía teclear HTML/JS en
  // el buscador y ejecutarlo en la sesión de quien viera este panel.
  const listaTop = document.getElementById("lista-top-consultas");
  const maxTop = maxDe(s.top_consultas, "veces");
  listaTop.innerHTML = s.top_consultas.length
    ? s.top_consultas.map((t) => filaConBarra(`${escaparHtml(t.consulta)} <span class="hint">(${t.veces})</span>`, t.veces, maxTop)).join("")
    : listaVacia;

  const listaSede = document.getElementById("lista-consultas-sede");
  const maxSede = maxDe(s.consultas_por_sede, "veces");
  listaSede.innerHTML = s.consultas_por_sede.length
    ? s.consultas_por_sede.map((c) => filaConBarra(`${escaparHtml(c.sede)} <span class="hint">(${c.veces})</span>`, c.veces, maxSede)).join("")
    : listaVacia;

  const listaArea = document.getElementById("lista-consultas-area");
  const maxArea = maxDe(s.consultas_por_area, "veces");
  listaArea.innerHTML = s.consultas_por_area.length
    ? s.consultas_por_area.map((c) => filaConBarra(`${escaparHtml(c.area)} <span class="hint">(${c.veces})</span>`, c.veces, maxArea)).join("")
    : listaVacia;

  const TIPO_LABEL = { jurisdiccional: "Jurisdiccional", administrativa: "Administrativa", servicio: "Servicio" };
  const listaTipo = document.getElementById("lista-consultas-tipo");
  const maxTipo = maxDe(s.consultas_por_tipo, "veces");
  listaTipo.innerHTML = s.consultas_por_tipo.length
    ? s.consultas_por_tipo
        .map((c) => filaConBarra(`${escaparHtml(TIPO_LABEL[c.tipo] || c.tipo)} <span class="hint">(${c.veces})</span>`, c.veces, maxTipo))
        .join("")
    : listaVacia;

  const listaSinResultado = document.getElementById("lista-top-sin-resultado");
  const maxSinResultado = maxDe(s.top_consultas_sin_resultado, "veces");
  listaSinResultado.innerHTML = s.top_consultas_sin_resultado.length
    ? s.top_consultas_sin_resultado
        .map((t) => {
          const boton = esAdmin()
            ? `<button type="button" class="btn secondary" style="padding:0.1rem 0.5rem; font-size:0.75rem; margin-top:0.4rem;" data-asignar="${escaparHtml(t.consulta)}">Asignar a un área</button>`
            : "";
          return (
            filaConBarra(`${escaparHtml(t.consulta)} <span class="hint">(${t.veces})</span>`, t.veces, maxSinResultado).replace("</li>", `${boton}</li>`)
          );
        })
        .join("")
    : '<li class="hint" style="list-style:none;">Sin búsquedas sin resultado todavía -- buena señal.</li>';
  listaSinResultado.querySelectorAll("[data-asignar]").forEach((b) =>
    b.addEventListener("click", () => abrirAsignarCobertura(b.dataset.asignar))
  );
  await cargarCobertura();

  const listaPendientes = document.getElementById("lista-pendientes-area");
  const maxPendientes = maxDe(s.pendientes_por_area, "cantidad");
  listaPendientes.innerHTML = s.pendientes_por_area.length
    ? s.pendientes_por_area
        .map((p) =>
          filaConBarra(
            `${escaparHtml(p.area)} <span class="hint">(${p.cantidad}, ${p.antiguedad_promedio_dias} días en promedio)</span>`,
            p.cantidad,
            maxPendientes
          )
        )
        .join("")
    : '<li class="hint" style="list-style:none;">No hay nada pendiente de aprobar en este momento.</li>';

  const listaCompletitud = document.getElementById("lista-completitud-area");
  listaCompletitud.innerHTML = s.completitud_por_area.length
    ? s.completitud_por_area
        .map((c) =>
          filaConBarra(
            `${escaparHtml(c.area)} <span class="hint">(${c.activas} activas, ${c.porcentaje_completo}% completo)</span>`,
            c.porcentaje_completo,
            100
          )
        )
        .join("")
    : '<li class="hint" style="list-style:none;">Todavía no hay dependencias publicadas.</li>';
}

// ═══════════════════════════════════════════════════════════
// SOLICITUDES DE COBERTURA -- cierra el ciclo del motor de
// descubrimiento: asigna a mano una búsqueda sin resultado a un área.
// ═══════════════════════════════════════════════════════════
const ESTADO_COBERTURA_LABEL = { pendiente: "Pendiente", en_progreso: "En progreso", resuelto: "Resuelto" };

async function cargarCobertura() {
  const box = document.getElementById("lista-cobertura");
  if (!box) return;
  try {
    const solicitudes = await api("/admin/cobertura");
    box.innerHTML = solicitudes.length
      ? solicitudes
          .map(
            (s) => `
        <li style="border:1px solid var(--line); border-radius:8px; padding:0.5rem 0.7rem; margin-bottom:0.4rem;">
          <strong>${escaparHtml(s.query_text)}</strong> <span class="hint">-- ${escaparHtml(s.area || "sin área")}</span>
          ${
            esAdmin()
              ? `<select data-cob-estado="${s.id}" style="margin-left:0.4rem; font-size:0.8rem;">
                  ${Object.entries(ESTADO_COBERTURA_LABEL)
                    .map(([v, t]) => `<option value="${v}" ${v === s.estado ? "selected" : ""}>${t}</option>`)
                    .join("")}
                </select>`
              : `<span class="badge ${s.estado === "resuelto" ? "activo" : "revision"}">${ESTADO_COBERTURA_LABEL[s.estado] || s.estado}</span>`
          }
          ${s.comentario ? `<div class="hint" style="margin-top:0.2rem;">${escaparHtml(s.comentario)}</div>` : ""}
        </li>`
          )
          .join("")
      : '<li class="hint" style="list-style:none;">Todavía no hay búsquedas asignadas a un área.</li>';
    box.querySelectorAll("[data-cob-estado]").forEach((sel) =>
      sel.addEventListener("change", async () => {
        try {
          await api(`/admin/cobertura/${sel.dataset.cobEstado}`, {
            method: "PUT",
            body: JSON.stringify({ estado: sel.value }),
          });
          mostrarToast("Estado actualizado.");
        } catch (err) {
          mostrarToast(err.message || "No se pudo actualizar el estado");
        }
      })
    );
  } catch {
    box.innerHTML = '<li class="hint" style="list-style:none;">No se pudo cargar.</li>';
  }
}

function abrirAsignarCobertura(queryText) {
  document.getElementById("cobertura-query").textContent = queryText;
  document.getElementById("form-cobertura").dataset.query = queryText;
  document.getElementById("cob-area").value = "";
  document.getElementById("cob-comentario").value = "";
  document.getElementById("cobertura-error").innerHTML = "";
  abrirModal("modal-cobertura", document.getElementById("cob-area"));
}
function cerrarModalCobertura() {
  cerrarModal("modal-cobertura");
}
document.getElementById("btn-cobertura-cancelar").addEventListener("click", cerrarModalCobertura);
configurarCierreModal("modal-cobertura", cerrarModalCobertura);
document.getElementById("form-cobertura").addEventListener("submit", async (e) => {
  e.preventDefault();
  const queryText = e.target.dataset.query;
  try {
    await api("/admin/cobertura", {
      method: "POST",
      body: JSON.stringify({
        query_text: queryText,
        area: document.getElementById("cob-area").value,
        comentario: document.getElementById("cob-comentario").value || null,
      }),
    });
    cerrarModalCobertura();
    await cargarCobertura();
    mostrarToast("Búsqueda asignada al área.");
  } catch (err) {
    document.getElementById("cobertura-error").innerHTML = `<p class="error-msg">${err.message}</p>`;
  }
});

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

  const selSedeTitulares = document.getElementById("t-sede");
  const actualTitulares = selSedeTitulares.value;
  selSedeTitulares.innerHTML =
    '<option value="">Todas las sedes que traiga el archivo</option>' +
    CACHE_SEDES.map((s) => `<option value="${escaparHtml(s.nombre)}">${escaparHtml(s.nombre)}</option>`).join("");
  selSedeTitulares.value = actualTitulares;
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
  abrirModal("modal-sede", document.getElementById("s-nombre"));
}

document.getElementById("btn-nueva-sede").addEventListener("click", () => {
  limpiarFormularioSede();
  abrirModal("modal-sede", document.getElementById("s-nombre"));
});
function cerrarModalSede() {
  limpiarFormularioSede();
  cerrarModal("modal-sede", document.getElementById("btn-nueva-sede"));
}
document.getElementById("btn-sede-cancelar").addEventListener("click", cerrarModalSede);
configurarCierreModal("modal-sede", cerrarModalSede);

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
    cerrarModal("modal-sede", document.getElementById("btn-nueva-sede"));
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
    const ultimo = u.ultimo_acceso ? fechaServidor(u.ultimo_acceso).toLocaleString("es-PE") : "Nunca";
    // Bloqueo automático tras intentos fallidos (ver app/crud/usuarios.py):
    // se muestra aparte de Activo/Inactivo porque es temporal y se levanta
    // solo con guardar la ficha desde "Editar", no con un interruptor propio.
    const bloqueado = u.bloqueado_hasta && fechaServidor(u.bloqueado_hasta) > new Date();
    const badgeBloqueo = bloqueado
      ? ` <span class="badge inactivo" title="Se levanta al guardar la ficha, o solo(a) al pasar la hora indicada">Bloqueada hasta ${fechaServidor(u.bloqueado_hasta).toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" })}</span>`
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
}

function cargarUsuarioEnFormulario(id) {
  const u = CACHE_USUARIOS.find((x) => x.id === id);
  if (!u) return;
  document.getElementById("form-usuario-titulo").textContent = `Editar: ${u.nombre}`;
  document.getElementById("u-id").value = u.id;
  document.getElementById("u-nombre").value = u.nombre;
  document.getElementById("u-email").value = u.email || "";
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

  abrirModal("modal-usuario", document.getElementById("u-nombre"));
}

document.getElementById("btn-nuevo-usuario").addEventListener("click", () => {
  limpiarFormularioUsuario();
  abrirModal("modal-usuario", document.getElementById("u-nombre"));
});
function cerrarModalUsuario() {
  limpiarFormularioUsuario();
  cerrarModal("modal-usuario", document.getElementById("btn-nuevo-usuario"));
}
document.getElementById("btn-usuario-cancelar").addEventListener("click", cerrarModalUsuario);
configurarCierreModal("modal-usuario", cerrarModalUsuario);

document.getElementById("form-usuario").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("u-id").value;
  try {
    if (id) {
      const payload = {
        nombre: document.getElementById("u-nombre").value,
        email: document.getElementById("u-email").value || null,
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
        email: document.getElementById("u-email").value || null,
        password: document.getElementById("u-password").value,
        rol: document.getElementById("u-rol").value,
        area: document.getElementById("u-area").value || null,
      };
      await api("/admin/usuarios", { method: "POST", body: JSON.stringify(payload) });
    }
    limpiarFormularioUsuario();
    cerrarModal("modal-usuario", document.getElementById("btn-nuevo-usuario"));
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

// Semáforo de vigencia: verde ≤90 días desde la última actualización,
// ámbar 91-180, rojo más de 180 -- mismos umbrales del Plan Maestro
// (sección "Diseño Técnico: Semáforo de Vigencia"). No necesita ningún dato
// nuevo: actualizado_en ya viene en cada dependencia desde el primer día.
function semaforoVigencia(actualizadoEn, validadoPor) {
  let base;
  if (!actualizadoEn) base = { clase: "rojo", texto: "Sin fecha registrada" };
  else {
    const dias = Math.floor((Date.now() - fechaServidor(actualizadoEn).getTime()) / 86400000);
    if (dias <= 90) base = { clase: "verde", texto: `Actualizado hace ${dias} día${dias === 1 ? "" : "s"}` };
    else if (dias <= 180) base = { clase: "ambar", texto: `Sin revisar hace ${dias} días` };
    else base = { clase: "rojo", texto: `Sin revisar hace ${dias} días` };
  }
  if (validadoPor) base.texto += ` · Validado por ${validadoPor}`;
  return base;
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
    : '<tr><td colspan="6" class="hint" style="padding:1rem;">Sin resultados.</td></tr>';
  for (const d of CACHE_DEPS) {
    const tr = document.createElement("tr");
    const nombreSede = d.sede ? d.sede.nombre : "—";
    const sem = semaforoVigencia(d.actualizado_en, d.validado_por);
    tr.innerHTML = `
      <td>${d.nombre}</td>
      <td>${d.tipo}</td>
      <td>${nombreSede}${d.piso ? " · piso " + d.piso : ""}</td>
      <td>${estadoBadge(d.estado)}</td>
      <td><span class="semaforo ${sem.clase}" title="${sem.texto}"></span> <span class="hint">${sem.texto}</span></td>
      <td class="actions">
        <button class="btn secondary" data-editar="${d.id}">Editar</button>
        <button class="btn secondary" data-qr="${d.id}">QR</button>
        <button class="btn secondary" data-historial="${d.id}">Historial</button>
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
  tbody.querySelectorAll("[data-historial]").forEach((b) =>
    b.addEventListener("click", () => abrirHistorial(parseInt(b.dataset.historial)))
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
  document.getElementById("f-titular").value = d.titular || "";
  document.getElementById("f-validado-por").value = d.validado_por || "";
  document.getElementById("f-proxima-revision").value = d.proxima_revision ? d.proxima_revision.slice(0, 10) : "";
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

  abrirModal("modal-dependencia", document.getElementById("f-nombre"));
}

document.getElementById("btn-nueva-dependencia").addEventListener("click", () => {
  limpiarFormulario();
  abrirModal("modal-dependencia", document.getElementById("f-nombre"));
});
function cerrarModalDependencia() {
  limpiarFormulario();
  cerrarModal("modal-dependencia", document.getElementById("btn-nueva-dependencia"));
}
document.getElementById("btn-cancelar").addEventListener("click", cerrarModalDependencia);
configurarCierreModal("modal-dependencia", cerrarModalDependencia);

document.getElementById("btn-aprobar").addEventListener("click", async () => {
  const id = document.getElementById("f-id").value;
  if (!id) return;
  try {
    await api(`/admin/dependencias/${id}/aprobar`, { method: "POST" });
    limpiarFormulario();
    cerrarModal("modal-dependencia", document.getElementById("btn-nueva-dependencia"));
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
    cerrarModal("modal-dependencia", document.getElementById("btn-nueva-dependencia"));
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
    titular: document.getElementById("f-titular").value || null,
    validado_por: document.getElementById("f-validado-por").value || null,
    proxima_revision: document.getElementById("f-proxima-revision").value || null,
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
    cerrarModal("modal-dependencia", document.getElementById("btn-nueva-dependencia"));
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
    const fecha = fechaServidor(r.fecha).toLocaleString("es-PE");
    // El detalle puede contener texto libre que alguien más escribió (nombre
    // de una dependencia, motivo de un rechazo...) -- escaparHtml() evita que
    // se ejecute como HTML/JS en la sesión de quien lea la auditoría.
    tr.innerHTML = `<td>${fecha}</td><td>${escaparHtml(r.usuario_dni) || "—"}</td><td>${escaparHtml(r.entidad) || "—"}</td>` +
      `<td><span class="badge ${r.accion.toLowerCase()}">${escaparHtml(r.accion)}</span></td>` +
      `<td>${escaparHtml(r.detalle)}</td>`;
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

// ═══════════════════════════════════════════════════════════
// MAPA INTERNO -- nodos y conexiones (wayfinding auto-declarado, Fase 4)
// ═══════════════════════════════════════════════════════════
let CACHE_NODOS = [];
let CACHE_CONEXIONES = [];
let _debounceMapaPiso;

async function poblarSelectorSedesMapa() {
  const sel = document.getElementById("mapa-sede");
  if (!sel) return;
  sel.innerHTML = CACHE_SEDES.map((s) => `<option value="${s.id}">${escaparHtml(s.nombre)}</option>`).join("");
  sel.addEventListener("change", cargarMapa);
  document.getElementById("mapa-piso").addEventListener("input", () => {
    clearTimeout(_debounceMapaPiso);
    _debounceMapaPiso = setTimeout(cargarMapa, 300);
  });
  if (CACHE_SEDES.length) await cargarMapa();
}

async function cargarMapa() {
  const sedeId = document.getElementById("mapa-sede").value;
  if (!sedeId) return;
  const piso = document.getElementById("mapa-piso").value.trim();
  const params = new URLSearchParams({ sede_id: sedeId });
  if (piso) params.set("piso", piso);
  [CACHE_NODOS, CACHE_CONEXIONES] = await Promise.all([
    api(`/admin/mapa/nodos?${params}`),
    api(`/admin/mapa/conexiones?sede_id=${sedeId}`),
  ]);
  const nodosPorId = Object.fromEntries(CACHE_NODOS.map((n) => [n.id, n]));

  const tbodyN = document.querySelector("#tabla-nodos tbody");
  tbodyN.innerHTML = CACHE_NODOS.length
    ? CACHE_NODOS.map((n) => {
        const dep = n.dependencia_id ? CACHE_DEPS.find((d) => d.id === n.dependencia_id) : null;
        return `<tr>
          <td>${escaparHtml(n.nombre)}</td>
          <td>${escaparHtml(n.piso || "—")}</td>
          <td>${n.es_punto_partida ? "Sí" : "No"}</td>
          <td>${dep ? escaparHtml(dep.nombre) : n.dependencia_id ? `Id ${n.dependencia_id}` : "—"}</td>
          <td class="actions">
            <button class="btn secondary" data-editar-nodo="${n.id}">Editar</button>
            <button class="btn secondary" data-eliminar-nodo="${n.id}">Eliminar</button>
          </td>
        </tr>`;
      }).join("")
    : '<tr><td colspan="5" class="hint" style="padding:1rem;">Sin nodos todavía para esta sede/piso.</td></tr>';
  tbodyN.querySelectorAll("[data-editar-nodo]").forEach((b) =>
    b.addEventListener("click", () => abrirNodo(parseInt(b.dataset.editarNodo)))
  );
  tbodyN.querySelectorAll("[data-eliminar-nodo]").forEach((b) =>
    b.addEventListener("click", () => eliminarNodo(parseInt(b.dataset.eliminarNodo)))
  );

  const tbodyC = document.querySelector("#tabla-conexiones tbody");
  tbodyC.innerHTML = CACHE_CONEXIONES.length
    ? CACHE_CONEXIONES.map(
        (c) => `<tr>
          <td>${escaparHtml(nodosPorId[c.nodo_a_id]?.nombre || `Id ${c.nodo_a_id}`)}</td>
          <td>${escaparHtml(nodosPorId[c.nodo_b_id]?.nombre || `Id ${c.nodo_b_id}`)}</td>
          <td>${c.distancia}</td>
          <td>${escaparHtml(c.instruccion_a_b || "—")}</td>
          <td>${escaparHtml(c.instruccion_b_a || "—")}</td>
          <td class="actions">
            <button class="btn secondary" data-editar-conexion="${c.id}">Editar</button>
            <button class="btn secondary" data-eliminar-conexion="${c.id}">Eliminar</button>
          </td>
        </tr>`
      ).join("")
    : '<tr><td colspan="6" class="hint" style="padding:1rem;">Sin conexiones todavía.</td></tr>';
  tbodyC.querySelectorAll("[data-editar-conexion]").forEach((b) =>
    b.addEventListener("click", () => abrirConexion(parseInt(b.dataset.editarConexion)))
  );
  tbodyC.querySelectorAll("[data-eliminar-conexion]").forEach((b) =>
    b.addEventListener("click", () => eliminarConexion(parseInt(b.dataset.eliminarConexion)))
  );
}

async function poblarDependenciasDelNodo(sedeId, seleccionadoId) {
  const sel = document.getElementById("n-dependencia");
  sel.innerHTML = '<option value="">— Ninguna —</option>';
  if (!sedeId) return;
  try {
    const deps = await (await fetch(`${API}/sedes/${sedeId}/dependencias`)).json();
    sel.innerHTML += deps.map((d) => `<option value="${d.id}">${escaparHtml(d.nombre)}</option>`).join("");
    if (seleccionadoId) sel.value = String(seleccionadoId);
  } catch {
    // Sin conexión momentánea: se guarda igual, solo sin dependencia vinculada.
  }
}

function limpiarFormularioNodo() {
  document.getElementById("nodo-titulo").textContent = "Nuevo nodo";
  document.getElementById("n-id").value = "";
  document.getElementById("form-nodo").reset();
  document.getElementById("n-sede").innerHTML = CACHE_SEDES.map((s) => `<option value="${s.id}">${escaparHtml(s.nombre)}</option>`).join("");
  document.getElementById("n-sede").value = document.getElementById("mapa-sede").value || "";
  document.getElementById("n-piso").value = document.getElementById("mapa-piso").value || "";
  document.getElementById("n-punto-partida").checked = true;
  document.getElementById("nodo-error").innerHTML = "";
  poblarDependenciasDelNodo(document.getElementById("n-sede").value, null);
}

function abrirNodo(id) {
  limpiarFormularioNodo();
  if (id) {
    const n = CACHE_NODOS.find((x) => x.id === id);
    if (n) {
      document.getElementById("nodo-titulo").textContent = `Editar: ${n.nombre}`;
      document.getElementById("n-id").value = n.id;
      document.getElementById("n-sede").value = n.sede_id;
      document.getElementById("n-piso").value = n.piso || "";
      document.getElementById("n-nombre").value = n.nombre;
      document.getElementById("n-punto-partida").checked = n.es_punto_partida;
      document.getElementById("n-pos-x").value = n.pos_x ?? "";
      document.getElementById("n-pos-y").value = n.pos_y ?? "";
      poblarDependenciasDelNodo(n.sede_id, n.dependencia_id);
    }
  }
  abrirModal("modal-nodo", document.getElementById("n-nombre"));
}
document.getElementById("btn-nuevo-nodo").addEventListener("click", () => abrirNodo(null));
document.getElementById("n-sede").addEventListener("change", (e) => poblarDependenciasDelNodo(e.target.value, null));
function cerrarModalNodo() {
  cerrarModal("modal-nodo", document.getElementById("btn-nuevo-nodo"));
}
document.getElementById("btn-nodo-cancelar").addEventListener("click", cerrarModalNodo);
configurarCierreModal("modal-nodo", cerrarModalNodo);

document.getElementById("form-nodo").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("n-id").value;
  const payload = {
    sede_id: parseInt(document.getElementById("n-sede").value),
    piso: document.getElementById("n-piso").value || null,
    nombre: document.getElementById("n-nombre").value,
    es_punto_partida: document.getElementById("n-punto-partida").checked,
    dependencia_id: document.getElementById("n-dependencia").value
      ? parseInt(document.getElementById("n-dependencia").value)
      : null,
    pos_x: document.getElementById("n-pos-x").value ? parseFloat(document.getElementById("n-pos-x").value) : null,
    pos_y: document.getElementById("n-pos-y").value ? parseFloat(document.getElementById("n-pos-y").value) : null,
  };
  try {
    await api(id ? `/admin/mapa/nodos/${id}` : "/admin/mapa/nodos", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    cerrarModalNodo();
    await cargarMapa();
    mostrarToast("Nodo guardado.");
  } catch (err) {
    document.getElementById("nodo-error").innerHTML = `<p class="error-msg">${err.message}</p>`;
  }
});

async function eliminarNodo(id) {
  const n = CACHE_NODOS.find((x) => x.id === id);
  if (!n || !confirm(`¿Eliminar el nodo "${n.nombre}"? También se borran sus conexiones.`)) return;
  try {
    await api(`/admin/mapa/nodos/${id}`, { method: "DELETE" });
    await cargarMapa();
    mostrarToast("Nodo eliminado.");
  } catch (err) {
    mostrarToast(err.message || "No se pudo eliminar el nodo");
  }
}

function limpiarFormularioConexion() {
  document.getElementById("conexion-titulo").textContent = "Nueva conexión";
  document.getElementById("c-id").value = "";
  document.getElementById("form-conexion").reset();
  const opciones = CACHE_NODOS.map((n) => `<option value="${n.id}">${escaparHtml(n.nombre)}${n.piso ? " (piso " + escaparHtml(n.piso) + ")" : ""}</option>`).join("");
  document.getElementById("c-nodo-a").innerHTML = opciones;
  document.getElementById("c-nodo-b").innerHTML = opciones;
  document.getElementById("c-distancia").value = "1";
  document.getElementById("conexion-error").innerHTML = "";
}

function abrirConexion(id) {
  if (!CACHE_NODOS.length) {
    mostrarToast("Primero crea al menos dos nodos en esta sede.");
    return;
  }
  limpiarFormularioConexion();
  if (id) {
    const c = CACHE_CONEXIONES.find((x) => x.id === id);
    if (c) {
      document.getElementById("conexion-titulo").textContent = "Editar conexión";
      document.getElementById("c-id").value = c.id;
      document.getElementById("c-nodo-a").value = c.nodo_a_id;
      document.getElementById("c-nodo-b").value = c.nodo_b_id;
      document.getElementById("c-distancia").value = c.distancia;
      document.getElementById("c-instr-ab").value = c.instruccion_a_b || "";
      document.getElementById("c-instr-ba").value = c.instruccion_b_a || "";
    }
  }
  abrirModal("modal-conexion", document.getElementById("c-nodo-a"));
}
document.getElementById("btn-nueva-conexion").addEventListener("click", () => abrirConexion(null));
function cerrarModalConexion() {
  cerrarModal("modal-conexion", document.getElementById("btn-nueva-conexion"));
}
document.getElementById("btn-conexion-cancelar").addEventListener("click", cerrarModalConexion);
configurarCierreModal("modal-conexion", cerrarModalConexion);

document.getElementById("form-conexion").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("c-id").value;
  const nodoA = document.getElementById("c-nodo-a").value;
  const nodoB = document.getElementById("c-nodo-b").value;
  if (nodoA === nodoB) {
    document.getElementById("conexion-error").innerHTML = `<p class="error-msg">Un nodo no puede conectarse consigo mismo.</p>`;
    return;
  }
  const payload = {
    nodo_a_id: parseInt(nodoA),
    nodo_b_id: parseInt(nodoB),
    distancia: parseInt(document.getElementById("c-distancia").value) || 1,
    instruccion_a_b: document.getElementById("c-instr-ab").value || null,
    instruccion_b_a: document.getElementById("c-instr-ba").value || null,
  };
  try {
    await api(id ? `/admin/mapa/conexiones/${id}` : "/admin/mapa/conexiones", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    cerrarModalConexion();
    await cargarMapa();
    mostrarToast("Conexión guardada.");
  } catch (err) {
    document.getElementById("conexion-error").innerHTML = `<p class="error-msg">${err.message}</p>`;
  }
});

async function eliminarConexion(id) {
  if (!confirm("¿Eliminar esta conexión?")) return;
  try {
    await api(`/admin/mapa/conexiones/${id}`, { method: "DELETE" });
    await cargarMapa();
    mostrarToast("Conexión eliminada.");
  } catch (err) {
    mostrarToast(err.message || "No se pudo eliminar la conexión");
  }
}

async function cargarTodo() {
  // El rol "consulta" no ve las pestañas de gestión del catálogo (ver
  // mostrarApp) y el backend rechaza /admin/dependencias, /admin/sedes de
  // escritura y /admin/usuarios para ese rol -- pedir esos datos igual sería
  // un viaje de red desperdiciado, y en el caso de dependencias, un error
  // 403 innecesario en la consola. Sí puede leer auditoría y duplicados
  // (cargarAuditoria ya hace ambos), por eso se pide aparte.
  if (esSoloConsulta()) {
    await Promise.all([cargarStats(), cargarAuditoria()]);
    return;
  }
  await cargarSedes();
  limpiarFormulario();
  limpiarFormularioUsuario();
  depSkip = 0;
  document.getElementById("filtro-nombre").value = "";
  await Promise.all([cargarStats(), cargarDependencias(), cargarAuditoria(), cargarUsuarios()]);
  if (esAdmin()) await poblarSelectorSedesMapa();
}

iniciar();
