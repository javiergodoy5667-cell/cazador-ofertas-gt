/* Cazador GT — service worker.
   Guarda la app y la ultima lista de ofertas para verla SIN internet. */
const CACHE = "cazador-gt-v1";
const CORE = [
  "./",
  "./index.html",
  "./style.css",
  "./app.js",
  "./manifest.json",
  "./icon.svg",
  "./icon-192.png",
  "./icon-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => c.addAll(CORE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);

  // Datos: primero red (frescos) y, si no hay internet, la copia en cache.
  if (/\.json$/.test(url.pathname)) {
    e.respondWith(
      fetch(e.request)
        .then((resp) => {
          const copia = resp.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copia));
          return resp;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // App (HTML/CSS/JS/iconos): cache primero, red como respaldo.
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request))
  );
});
