# -*- coding: utf-8 -*-
"""
Recolector de PriceSmart Guatemala con navegador automatico (Playwright).
PriceSmart muestra precios a cualquier visitante (sin cuenta), pero los pinta
con JavaScript, asi que se abre cada categoria como lo haria una persona.
- Categorias raiz de /es-gt/categorias (robots.txt solo prohibe ?fq=, carrito
  y cuenta). 12 productos por pagina; se pasa de pagina con clic en el numero.
- Tarjeta: .sf-price con sf-price__regular (precio), sf-price__special
  (precio con descuento) y sf-price__old (precio antes; oculto con
  display-none si no hay descuento).
- Si Playwright no esta instalado, falla solo esta tienda.
"""
import re
import time

from . import _base

HOST = "www.pricesmart.com"
TIENDA = "PriceSmart"
SLUG = "pricesmart"
BASE = f"https://{HOST}"
PRIORIDAD = ["Electronicos", "Computadoras", "Celulares", "Electrodomesticos",
             "Linea-blanca", "Herramientas", "Automotriz", "Ferreteria", "Hogar"]
CATEGORIAS_POR_CORRIDA = 8
PAGINAS_MAX = 25

JS = r"""() => [...document.querySelectorAll('.sf-price')].map(pr => {
  let c = pr;
  while (c && !c.querySelector("a[href*='/es-gt/producto/']")) c = c.parentElement;
  if (!c) return null;
  const a = c.querySelector("a[href*='/es-gt/producto/']");
  const vis = sel => { const e = pr.querySelector(sel);
    return e && !e.classList.contains('display-none') ? e.innerText : null; };
  const img = c.querySelector('img');
  return {href: a.getAttribute('href'),
          nombre: (c.querySelector('[class*=title],h3,h2') || a).innerText.trim(),
          regular: vis('.sf-price__regular'), especial: vis('.sf-price__special'),
          antes: vis('.sf-price__old'), imagen: img ? img.src : null,
          agotado: /agotado|no disponible/i.test(c.innerText)};
}).filter(Boolean)"""


def _categorias():
    st, _fu, html = _base.get(f"{BASE}/es-gt/categorias", host=HOST)
    if st != 200 or not html:
        return []
    cats = sorted(set(re.findall(r'href="(/es-gt/categoria/[^"?]+)"', html)))

    def orden(c):
        return next((n for n, p in enumerate(PRIORIDAD) if p.lower() in c.lower()), len(PRIORIDAD))
    return sorted(cats, key=orden)


def _turno(cats):
    """Las 4 primeras (de alerta) siempre; las demas rotan por hora."""
    import datetime as dt
    fijas, resto = cats[:4], cats[4:]
    cupo = CATEGORIAS_POR_CORRIDA - len(fijas)
    if not resto or cupo <= 0:
        return fijas
    ini = (dt.datetime.utcnow().hour * cupo) % len(resto)
    return fijas + (resto + resto)[ini:ini + cupo]


def _producto(d, ruta):
    precio = _base.limpiar_precio(d.get("especial") or d.get("regular"))
    if not precio or precio <= 0:
        return None
    antes = _base.limpiar_precio(d.get("antes"))
    m = re.search(r"/(\d+)/?$", d.get("href") or "")
    if not m:
        return None
    return _base.nuevo_producto(
        id_=f"{SLUG}-{m.group(1)}", tienda=TIENDA, nombre=d.get("nombre", ""),
        precio=precio, antes=antes if antes and antes > precio else None,
        url=BASE + d["href"], imagen=d.get("imagen"),
        categoria=ruta.split("/")[3] if ruta.count("/") >= 3 else ruta,
        disponible=not d.get("agotado"), modo_compra="club", modelo=m.group(1))


def _abrir_navegador(p):
    try:
        return p.chromium.launch(headless=True)
    except Exception:
        return p.chromium.launch(channel="chrome", headless=True)  # PC con Chrome


def recolectar(tiempo_limite=420):
    from playwright.sync_api import sync_playwright
    inicio = time.monotonic()
    vistos = {}
    cats = _turno(_categorias())
    with sync_playwright() as p:
        nav = _abrir_navegador(p)
        pg = nav.new_page(locale="es-GT")
        for ruta in cats:
            if time.monotonic() - inicio > tiempo_limite:
                break
            try:
                pg.goto(BASE + ruta, wait_until="domcontentloaded", timeout=60000)
                pg.wait_for_selector(".sf-price", timeout=30000)
            except Exception:
                continue
            for pagina in range(1, PAGINAS_MAX + 1):
                nuevos = 0
                for d in pg.evaluate(JS):
                    prod = _producto(d, ruta)
                    if prod and prod["id"] not in vistos:
                        vistos[prod["id"]] = prod
                        nuevos += 1
                siguiente = pg.locator(f"text='{pagina + 1}'")
                if not nuevos or siguiente.count() == 0 or time.monotonic() - inicio > tiempo_limite:
                    break
                try:
                    siguiente.first.click()
                    time.sleep(3)  # cortesia + carga
                except Exception:
                    break
        nav.close()
    return list(vistos.values())
