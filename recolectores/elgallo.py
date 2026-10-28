# -*- coding: utf-8 -*-
"""
Recolector de El Gallo más Gallo Guatemala (Magento, HTML).
robots.txt prohibe URLs con "?" -> solo la pagina 1 (20 productos) de cada
categoria. Se leen las paginas cortas de la portada (/celulares-y-tablets,
/computadoras...) y las subcategorias finales del menu /productos/...
Cada tarjeta: a.product-item-link (nombre, url) y data-price-amount con
data-price-type finalPrice (actual) / oldPrice (habitual).
"""
import html as htmllib
import re
import time

from . import _base

HOST = "www.elgallomasgallo.com.gt"
TIENDA = "El Gallo más Gallo"
SLUG = "elgallo"
BASE = f"https://{HOST}"
PRIORIDAD = ["celulares", "tv-", "computadoras", "audio", "linea-blanca",
             "hogar-y-linea-blanca", "videojuegos", "electrodomesticos", "motos"]
CORTAS = ["shopper-de-promociones", "celulares-y-tablets", "tv-y-entretenimiento",
          "computadoras", "hogar-y-linea-blanca"]


def _hojas():
    st, _fu, html = _base.get(f"{BASE}/productos", host=HOST)
    if st != 200 or not html:
        return []
    rutas = sorted(set(re.findall(r'href="https://www\.elgallomasgallo\.com\.gt/(productos/[a-z0-9/-]+)"', html)))
    hojas = [r for r in rutas if not any(o.startswith(r + "/") for o in rutas)]
    hojas = CORTAS + hojas

    def orden(r):
        return next((n for n, p in enumerate(PRIORIDAD) if p in r), len(PRIORIDAD))
    return sorted(hojas, key=orden)


def _tarjetas(html, ruta):
    out = []
    for b in html.split("product-item-info")[1:]:
        a = re.search(r'<a title="([^"]*)" href="([^"]+)" class="product-item-link"', b)
        if not a:
            continue
        precios = dict((t, _base.limpiar_precio(v)) for v, t in re.findall(
            r'data-price-amount="([\d.]+)" data-price-type="(\w+)"', b))
        precio = precios.get("finalPrice")
        if not precio or precio <= 0:
            continue
        precio = round(precio, 2)
        antes = round(precios["oldPrice"], 2) if precios.get("oldPrice") else None
        m = re.search(r"-(\d{5,})$", a.group(2))
        img = re.search(r'<img[^>]+src="(https://[^"]+/media/catalog/product/[^"]+)"', b)
        out.append(_base.nuevo_producto(
            id_=f"{SLUG}-{m.group(1) if m else a.group(2).rsplit('/', 1)[-1]}",
            tienda=TIENDA, nombre=htmllib.unescape(a.group(1)).strip(), precio=precio,
            antes=antes if antes and antes > precio + 0.01 else None, url=a.group(2),
            imagen=img.group(1) if img else None, categoria=ruta))
    return out


def recolectar(tiempo_limite=420):
    inicio = time.monotonic()
    vistos = {}
    for ruta in _hojas():
        if time.monotonic() - inicio > tiempo_limite:
            break
        st, _fu, html = _base.get(f"{BASE}/{ruta}", host=HOST)
        if st != 200 or not html:
            continue
        for p in _tarjetas(html, ruta):
            vistos.setdefault(p["id"], p)
    return list(vistos.values())
