# -*- coding: utf-8 -*-
"""
Recolector de La Curacao Guatemala (Magento).
Cada pagina de categoria embebe un <script type="application/ld+json"> con un
ARRAY de productos (name, offers[].price, url, image). Se descubren las
categorias desde la portada y se pagina cada una (?p=1,2,...).
"""
import json
import re
import time

from . import _base

HOST = "lacuracaonline.com"
TIENDA = "La Curacao"
SLUG = "lacuracao"
BASE = "https://lacuracaonline.com/guatemala"
MEDIA = "https://www.lacuracaonline.com/media/catalog/product"

CATEGORIAS_RESERVA = ["muebles", "electrodomesticos", "celulares", "computo",
                      "televisores", "camas", "refrigeradoras", "lavadoras",
                      "audio", "videojuegos"]


def _imagen(url):
    if not url:
        return None
    if url.startswith("http"):
        return url
    if url.startswith("/"):
        if "/media/" in url:
            return "https://www.lacuracaonline.com" + url
        return MEDIA + url
    return url


def _id_estable(url):
    m = re.search(r"-(\d{6,})/p/?$", url or "")
    if m:
        return f"{SLUG}-{m.group(1)}"
    return f"{SLUG}-{abs(hash(url)) if url else 'x'}"


def _extraer_productos(html):
    out = []
    for bloque in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
                             html, re.S):
        try:
            obj = json.loads(bloque)
        except Exception:
            continue
        objs = obj if isinstance(obj, list) else [obj]
        for o in objs:
            if not (isinstance(o, dict) and o.get("@type") == "Product"):
                continue
            offers = o.get("offers") or []
            if isinstance(offers, dict):
                offers = [offers]
            if not offers:
                continue
            off = offers[0]
            precio = _base.limpiar_precio(off.get("price"))
            if precio is None or precio <= 0:
                continue
            url = off.get("url") or o.get("url") or ""
            disp = "InStock" in str(off.get("availability", ""))
            out.append(_base.nuevo_producto(
                id_=_id_estable(url), tienda=TIENDA, nombre=o.get("name", ""),
                precio=precio, antes=None, url=url,
                imagen=_imagen(o.get("image")), categoria="",
                disponible=disp, modo_compra="en_linea"))
    return out


def _descubrir_categorias():
    st, _fu, html = _base.get(BASE + "/", host=HOST)
    if st != 200 or not html:
        return CATEGORIAS_RESERVA
    slugs = re.findall(r'/guatemala/c/([a-z0-9-]+)', html)
    unicos = list(dict.fromkeys(slugs))
    return unicos[:30] if unicos else CATEGORIAS_RESERVA


def recolectar():
    inicio = time.monotonic()
    vistos = {}
    for slug in _descubrir_categorias():
        if time.monotonic() - inicio > 300:
            break
        for p in (1, 2, 3, 4, 5):
            if time.monotonic() - inicio > 300:
                break
            url = f"{BASE}/c/{slug}" if p == 1 else f"{BASE}/c/{slug}?p={p}"
            st, _fu, html = _base.get(url, host=HOST)
            if st != 200 or not html:
                break
            nuevos = _extraer_productos(html)
            if not nuevos and p == 1:
                break
            for prod in nuevos:
                if prod["url"] and prod["url"] not in vistos:
                    vistos[prod["url"]] = prod
            if len(nuevos) < 18:
                break
    return list(vistos.values())
