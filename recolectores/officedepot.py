# -*- coding: utf-8 -*-
"""
Recolector de Office Depot Guatemala (SAP Hybris, HTML).
Las 8 categorias raiz (/c/0N-0-0-0) se paginan con
?q=:relevance&page=N&pageSize=100 (robots.txt lo permite).
Cada tarjeta trae: form addToCartForm<codigo> con productNamePost, y un boton
con data-productcart (precio normal) y data-productdiscounted (precio actual).
"""
import html as htmllib
import re
import time

from . import _base

HOST = "www.officedepot.com.gt"
TIENDA = "Office Depot"
SLUG = "officedepot"
BASE = f"https://{HOST}/officedepotGuatemala/en"
# Electronica primero; luego el resto.
CATEGORIAS = ["05", "04", "06", "07", "08", "03", "02", "01"]
POR_PAGINA = 100
MAX_PAGINAS = 15


def _tarjetas(html):
    out = {}
    for m in re.finditer(r'<form id="addToCartForm(\d+)"(.*?)</form>', html, re.S):
        codigo, b = m.group(1), m.group(2)
        nm = re.search(r'name="productNamePost" value="([^"]*)"', b)
        if not nm:
            continue
        out[codigo] = {"nombre": htmllib.unescape(nm.group(1)).strip()}
    for m in re.finditer(r"data-productcart='Q([\d,.]+)'\s+data-productdiscounted='Q([\d,.]+)'"
                         r"\s+data-productcode='(\d+)'", html):
        if m.group(3) in out:
            out[m.group(3)]["normal"] = _base.limpiar_precio(m.group(1))
            out[m.group(3)]["actual"] = _base.limpiar_precio(m.group(2))
    for m in re.finditer(r'action="(/officedepotGuatemala/en/[^"]+/p/(\d+))/configuratorPage/"', html):
        if m.group(2) in out:
            out[m.group(2)]["url"] = f"https://{HOST}{m.group(1)}"
    for m in re.finditer(r"addToCartDatalayer\('(\d+)','[^']*','([^']*)','([^']*)'", html):
        if m.group(1) in out:
            out[m.group(1)].setdefault("cat", htmllib.unescape(m.group(2)))
            out[m.group(1)].setdefault("marca", htmllib.unescape(m.group(3)))
    return out


def recolectar(tiempo_limite=420):
    inicio = time.monotonic()
    vistos = {}
    for cat in CATEGORIAS:
        for pagina in range(MAX_PAGINAS):
            if time.monotonic() - inicio > tiempo_limite:
                return list(vistos.values())
            url = f"{BASE}/c/{cat}-0-0-0?q=%3Arelevance&page={pagina}&pageSize={POR_PAGINA}"
            st, _fu, html = _base.get(url, host=HOST, timeout=60)
            if st != 200 or not html:
                break
            tarjetas = _tarjetas(html)
            nuevos = 0
            for codigo, t in tarjetas.items():
                pid = f"{SLUG}-{codigo}"
                precio = t.get("actual") or t.get("normal")
                if pid in vistos or not precio or precio <= 0 or not t.get("url"):
                    continue
                normal = t.get("normal")
                vistos[pid] = _base.nuevo_producto(
                    id_=pid, tienda=TIENDA, nombre=t["nombre"], precio=precio,
                    antes=normal if normal and normal > precio else None,
                    url=t["url"], imagen=None, categoria=t.get("cat", ""),
                    disponible=True, marca=t.get("marca", ""), modelo=codigo)
                nuevos += 1
            if len(tarjetas) < POR_PAGINA or not nuevos:
                break
    return list(vistos.values())
