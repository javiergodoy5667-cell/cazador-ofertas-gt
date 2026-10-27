/* Cazador GT — service worker.
   App (index.html, app.js, style.css) con RED PRIMERO y cache como respaldo
   sin internet. JSON con red primero. Iconos con cache. */
const CACHE = "cazador-gt-v2";
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

function redPrimero(e) {
  return fetch(e.request)
    .then((resp) => {
      const copia = resp.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copia));
      return resp;
    })
    .catch(() => caches.match(e.request));
}

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);

  // App (HTML/JS/CSS) y raiz: RED primero, cache si no hay internet.
  if (/\.(html|js|css)$/.test(url.pathname) || url.pathname.endsWith("/")) {
    e.respondWith(redPrimero(e));
    return;
  }

  // Datos JSON: red primero (frescos), cache de respaldo.
  if (/\.json$/.test(url.pathname)) {
    e.respondWith(redPrimero(e));
    return;
  }

  // Iconos y demas: cache primero.
  e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request)));
});
