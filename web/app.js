/* Cazador GT — lógica de la página (sin dependencias). */
"use strict";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g,
  (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const ORDEN_NIVEL = { error: 0, loca: 1, muy_buena: 2, buena: 3, agotado: 9 };
const TOP_POR_CATEGORIA = 5;

const state = {
  ofertas: [],
  precios: {},
  categoria: localStorage.getItem("cazador_cat") || ""
};

function formato(n) {
  if (n == null || isNaN(n)) return "0";
  return Number(n).toLocaleString("es-GT", { maximumFractionDigits: 0 });
}

async function cargar() {
  try {
    const [o, p] = await Promise.all([
      fetch("ofertas.json").then((r) => r.json()),
      fetch("precios.json").then((r) => r.json()).catch(() => ({}))
    ]);
    state.ofertas = Array.isArray(o) ? o : [];
    state.precios = p || {};
  } catch (e) {
    state.ofertas = [];
  }
  poblarFiltros();
  renderizar();
  actualizarPie();
}

function contarPorCategoria() {
  const m = {};
  for (const o of state.ofertas) {
    const c = o.categoria || "📦 Otros";
    m[c] = (m[c] || 0) + 1;
  }
  return m;
}

function poblarFiltros() {
  const tiendas = [...new Set(state.ofertas.map((o) => o.tienda).filter(Boolean))].sort();
  $("tienda").innerHTML = '<option value="">Todas las tiendas</option>' +
    tiendas.map((t) => `<option>${esc(t)}</option>`).join("");

  const conteo = contarPorCategoria();
  const cats = Object.keys(conteo).sort((a, b) => conteo[b] - conteo[a]);
  let html = `<button class="cat ${state.categoria === "" ? "activa" : ""}" data-cat="">Todas</button>`;
  for (const c of cats) {
    const emoji = c.split(" ")[0];
    const nombre = c.split(" ").slice(1).join(" ");
    html += `<button class="cat ${state.categoria === c ? "activa" : ""}" data-cat="${esc(c)}">${esc(emoji)} ${esc(nombre)} <span class="n">${conteo[c]}</span></button>`;
  }
  $("barra_categorias").innerHTML = html;
}

function filtradas() {
  const q = $("busqueda").value.trim().toLowerCase();
  const nivel = $("nivel").value;
  const tienda = $("tienda").value;
  const online = $("online").checked;
  const fisica = $("tienda_fisica").checked;
  const pmin = parseFloat($("precio_min").value);
  const pmax = parseFloat($("precio_max").value);

  return state.ofertas.filter((o) => {
    if (nivel && (ORDEN_NIVEL[o.nivel] ?? 9) > (ORDEN_NIVEL[nivel] ?? 9)) return false;
    if (tienda && o.tienda !== tienda) return false;
    if (online && o.modo_compra !== "en_linea") return false;
    if (fisica && o.modo_compra === "en_linea") return false;
    if (!isNaN(pmin) && o.precio_actual < pmin) return false;
    if (!isNaN(pmax) && o.precio_actual > pmax) return false;
    if (q && !((o.nombre || "").toLowerCase().includes(q) ||
               (o.tienda || "").toLowerCase().includes(q))) return false;
    return true;
  });
}

function ordenar(lista) {
  const ord = $("orden").value;
  if (ord === "ahorro") return [...lista].sort((a, b) => b.ahorro_q - a.ahorro_q);
  if (ord === "reciente") return [...lista].sort((a, b) => (b.visto_en || "").localeCompare(a.visto_en || ""));
  return [...lista].sort((a, b) => (b.puntaje || 0) - (a.puntaje || 0));
}

function renderizar() {
  const lista = ordenar(filtradas());
  if (state.categoria !== "") {
    const solo = lista.filter((o) => (o.categoria || "📦 Otros") === state.categoria);
    renderPlana(solo);
  } else {
    renderAgrupada(lista);
  }
}

function renderPlana(lista) {
  const grid = $("grid");
  grid.innerHTML = "";
  $("vacio").hidden = lista.length > 0;
  for (const o of lista) grid.appendChild(tarjeta(o));
}

function renderAgrupada(lista) {
  const grid = $("grid");
  grid.innerHTML = "";
  $("vacio").hidden = lista.length > 0;
  const por = {};
  for (const o of lista) {
    const c = o.categoria || "📦 Otros";
    (por[c] = por[c] || []).push(o);
  }
  const orden = Object.keys(por).sort((a, b) => por[b].length - por[a].length);
  for (const c of orden) {
    const seccion = document.createElement("section");
    seccion.className = "seccion";
    const emoji = c.split(" ")[0];
    const nombre = c.split(" ").slice(1).join(" ");
    seccion.innerHTML = `<h2 class="sec-titulo">${esc(emoji)} ${esc(nombre)}
      <span class="sec-n">${por[c].length}</span></h2>`;
    const cont = document.createElement("div");
    cont.className = "grid";
    for (const o of por[c].slice(0, TOP_POR_CATEGORIA)) cont.appendChild(tarjeta(o));
    seccion.appendChild(cont);
    if (por[c].length > TOP_POR_CATEGORIA) {
      const ver = document.createElement("button");
      ver.className = "ver-mas";
      ver.textContent = `Ver todos los de ${nombre} (${por[c].length})`;
      ver.addEventListener("click", () => { setCategoria(c); });
      seccion.appendChild(ver);
    }
    grid.appendChild(seccion);
  }
}

function setCategoria(c) {
  state.categoria = c;
  localStorage.setItem("cazador_cat", c);
  poblarFiltros();
  renderizar();
  $("barra_categorias").scrollLeft = 0;
}

function tarjeta(o) {
  const art = document.createElement("article");
  art.className = "tarjeta nivel-" + (o.nivel || "buena");
  art.addEventListener("click", () => abrirModal(o));
  const img = o.imagen
    ? `<img loading="lazy" src="${esc(o.imagen)}" alt="" onerror="this.style.display='none'">`
    : "";
  const desc = Math.round((o.descuento_real || 0) * 100);
  const modo = o.modo_compra === "en_linea" ? "🛒 en línea" : "🏪 en tienda";
  art.innerHTML = `
    ${img}
    <div class="badge">${esc(o.nivel_emoji || "")} ${esc(o.nivel_label || "")} · -${desc}%</div>
    <div class="contenido">
      <div class="nombre">${esc(o.nombre)}</div>
      <div class="precio">Q${formato(o.precio_actual)}</div>
      <div class="antes">antes ~Q${formato(o.precio_referencia)}</div>
      <div class="ahorro">Ahorras Q${formato(o.ahorro_q)}</div>
      <div class="meta">🏬 ${esc(o.tienda)} · ${modo}</div>
      <a class="boton" href="${esc(o.url)}" target="_blank" rel="noopener"
         onclick="event.stopPropagation()">Ver / Comprar</a>
    </div>`;
  return art;
}

function abrirModal(o) {
  $("modal_nombre").textContent = o.nombre;
  $("modal_precio").textContent =
    `Q${formato(o.precio_actual)} · −${Math.round((o.descuento_real || 0) * 100)}%`;
  $("modal_link").href = o.url || "#";
  dibujarGrafica(o.id);
  $("modal").hidden = false;
}

function dibujarGrafica(id) {
  const cont = $("modal_grafica");
  const serie = (state.precios[id] || []).slice(-30);
  if (serie.length < 2) {
    cont.innerHTML = "<p class='sinhist'>Aún no hay historial (se construye día a día).</p>";
    return;
  }
  const w = 320, h = 140, pad = 8;
  const vals = serie.map((s) => s.precio);
  const min = Math.min(...vals), max = Math.max(...vals);
  const rango = (max - min) || 1;
  const pts = serie.map((s, i) => {
    const x = pad + (i / (serie.length - 1)) * (w - 2 * pad);
    const y = h - pad - ((s.precio - min) / rango) * (h - 2 * pad);
    return [x.toFixed(1), y.toFixed(1)];
  });
  const poly = pts.map((p) => p.join(",")).join(" ");
  const dots = pts.map((p) => `<circle cx="${p[0]}" cy="${p[1]}" r="3" fill="#ff6a00"/>`).join("");
  cont.innerHTML = `
    <svg viewBox="0 0 ${w} ${h}" width="100%">
      <polyline points="${poly}" fill="none" stroke="#ff6a00" stroke-width="2.5"/>
      ${dots}
    </svg>
    <div class="hist-meta">${serie.length} observaciones · mín Q${formato(min)} · máx Q${formato(max)}</div>`;
}

function actualizarPie() {
  const ts = state.ofertas.map((o) => o.visto_en).filter(Boolean).sort().pop();
  if (ts) {
    const hora = String(ts).split("T")[1] ? String(ts).split("T")[1].slice(0, 5) : "";
    $("pie").textContent = `Última actualización: ${hora} (hora Guatemala)`;
  } else {
    $("pie").textContent = "Sin datos todavía.";
  }
}

function mpLink(termino) {
  return "https://www.facebook.com/marketplace/guatemala/search?query=" +
    encodeURIComponent(termino);
}

document.addEventListener("DOMContentLoaded", () => {
  $("nivel").innerHTML =
    '<option value="">Cualquier nivel</option>' +
    '<option value="error">🚨 Error de precio</option>' +
    '<option value="loca">🔥 Loca</option>' +
    '<option value="muy_buena">⚡ Muy buena</option>' +
    '<option value="buena">✅ Buena</option>';
  $("orden").innerHTML =
    '<option value="puntaje">Más loca primero</option>' +
    '<option value="ahorro">Mayor ahorro</option>' +
    '<option value="reciente">Más reciente</option>';

  ["busqueda", "nivel", "tienda", "orden", "online", "tienda_fisica",
   "precio_min", "precio_max"].forEach((id) => {
    $(id).addEventListener("input", renderizar);
    $(id).addEventListener("change", renderizar);
  });

  $("barra_categorias").addEventListener("click", (e) => {
    const b = e.target.closest(".cat");
    if (b) setCategoria(b.dataset.cat || "");
  });

  const abrirMp = () => {
    const t = $("mp_busqueda").value.trim();
    if (t) window.open(mpLink(t), "_blank", "noopener");
  };
  $("mp_boton").addEventListener("click", abrirMp);
  $("mp_busqueda").addEventListener("keydown", (e) => { if (e.key === "Enter") abrirMp(); });

  $("modal_cerrar").addEventListener("click", () => { $("modal").hidden = true; });
  $("modal").addEventListener("click", (e) => { if (e.target === $("modal")) $("modal").hidden = true; });

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("service-worker.js").catch(() => {});
  }
  cargar();
});
