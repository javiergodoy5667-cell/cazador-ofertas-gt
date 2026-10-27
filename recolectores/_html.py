# -*- coding: utf-8 -*-
"""
Recolector generico para tiendas con sitemap + microdatos ld+json
(Intelaf y Pacifiko). Descarga el sitemap, toma un numero fijo de URLs de
producto (deterministico para poder construir historial) y extrae el precio
del bloque ld+json tipo Product.
"""
import json
import re

from . import _base


def _ldjson_producto(body):
    """Extrae nombre/precio/imagen/disponible/url de ld+json. None si falla."""
    for b in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
                        body, re.S):
        try:
            obj = json.loads(b)
        except Exception:
            continue
        objs = obj if isinstance(obj, list) else [obj]
        for o in objs:
            if not (isinstance(o, dict) and o.get("@type") == "Product"):
                continue
            offers = o.get("offers")
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            if not offers:
                continue
            precio = _base.limpiar_precio(offers.get("price"))
            if precio is None or precio <= 0:
                continue
            img = o.get("image")
            if isinstance(img, list):
                img = img[0] if img else None
            disp = "InStock" in str(offers.get("availability", ""))
            categoria = o.get("category", "")
            return _base.nuevo_producto(
                id_="", tienda="", nombre=o.get("name", ""),
                precio=precio, antes=None,
                url=offers.get("url", ""), imagen=img, categoria=categoria,
                disponible=disp)
    return None


def recolectar_html_ldjson(slug, tienda, sitemap_url, filtro, host,
                           max_productos=40):
    status, _fu, body = _base.get(sitemap_url, host=host)
    if status != 200 or not body:
        return []
    locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", body)
    urls = [u.replace("&amp;", "&") for u in locs if filtro in u]
    out = []
    for u in urls:
        if len(out) >= max_productos:
            break
        st, fu, html = _base.get(u, host=host)
        if st != 200 or not html:
            continue
        d = _ldjson_producto(html)
        if not d:
            continue
        d["id"] = f"{slug}-{len(out)}"
        d["tienda"] = tienda
        d["url"] = d.get("url") or fu
        out.append(d)
    return out
