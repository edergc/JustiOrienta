// Service worker de Justicia Orienta -- modo offline esencial.
//
// Alcance deliberadamente acotado (ver Plan Maestro, Fase 4): deja
// disponible sin conexión la app y lo último que el ciudadano ya vio
// (sedes, dependencias de una sede visitada). NO promete que la búsqueda
// en vivo funcione sin internet -- eso requeriría duplicar el catálogo
// completo en el navegador, y hoy no es necesario: basta con que quien ya
// abrió la app y ya consultó su sede pueda seguir viéndola sin señal.

const CACHE_SHELL = "jo-shell-v1";
const CACHE_DATOS = "jo-datos-v1";

const ARCHIVOS_SHELL = [
  "/",
  "/css/styles.css",
  "/js/public.js",
  "/manifest.json",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_SHELL).then((cache) => cache.addAll(ARCHIVOS_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((nombres) =>
      Promise.all(
        nombres
          .filter((n) => n !== CACHE_SHELL && n !== CACHE_DATOS)
          .map((n) => caches.delete(n))
      )
    )
  );
  self.clients.claim();
});

// Solo se cachean lecturas (GET) de sedes y de "dependencias por sede" --
// exactamente lo que usa el tile "Estoy aquí". Nunca se cachea /buscar
// (resultado distinto por cada consulta) ni nada de /admin (requiere
// sesión y datos siempre al día, no una copia vieja).
function esDatoCacheable(url) {
  return (
    /\/api\/v1\/sedes\/?$/.test(url.pathname) ||
    /\/api\/v1\/sedes\/\d+\/dependencias$/.test(url.pathname)
  );
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (esDatoCacheable(url)) {
    // Red primero (el dato debe estar al día si hay conexión); si falla,
    // se sirve la última copia buena guardada.
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copia = res.clone();
          caches.open(CACHE_DATOS).then((cache) => cache.put(req, copia));
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  if (ARCHIVOS_SHELL.includes(url.pathname)) {
    // App shell: cache primero para que cargue instantáneo, con
    // actualización silenciosa en segundo plano.
    event.respondWith(
      caches.match(req).then((cacheada) => {
        const enRed = fetch(req)
          .then((res) => {
            const copia = res.clone();
            caches.open(CACHE_SHELL).then((cache) => cache.put(req, copia));
            return res;
          })
          .catch(() => cacheada);
        return cacheada || enRed;
      })
    );
  }
});
