# -*- coding: utf-8 -*-
"""
Recolector de EPA Guatemala (Magento, gt.epaenlinea.com).
GraphQL publico /graphql (robots.txt no lo prohibe): categoria 4 "Productos"
(~9,700), 100 por pagina. regular_price = precio normal, final_price = actual.
Los precios vienen con decimales largos (1998.998401) -> se redondean.
"""
import json
import time
import urllib.parse

from . import _base

HOST = "gt.epaenlinea.com"
TIENDA = "EPA"
SLUG = "epa"
CATEGORIA_PRODUCTOS = "4"
POR_PAGINA = 100
CAMPOS = ("total_count page_info{total_pages} items{name sku url_key url_suffix "
          "stock_status small_image{url} categories{name} "
          "price_range{minimum_price{regular_price{value currency} final_price{value}}}}")


def _pagina(n):
    q = ('{products(filter:{category_id:{eq:"%s"}},pageSize:%d,currentPage:%d){%s}}'
         % (CATEGORIA_PRODUCTOS, POR_PAGINA, n, CAMPOS))
    st, _fu, txt = _base.get(f"https://{HOST}/graphql?query=" + urllib.parse.quote(q),
                             host=HOST, timeout=60)
    if st != 200 or not txt:
        return None
    try:
        return json.loads(txt)["data"]["products"]
    except Exception:
        return None


def _producto(it):
    if not it:
        return None
    pr = (it.get("price_range") or {}).get("minimum_price") or {}
    regular = pr.get("regular_price") or {}
    if regular.get("currency") not in (None, "GTQ"):
        return None
    normal = round(regular.get("value") or 0, 2)
    precio = round((pr.get("final_price") or {}).get("value") or normal, 2)
    if precio <= 0:
        return None
    cats = [c.get("name", "") for c in it.get("categories") or []]
    return _base.nuevo_producto(
        id_=f"{SLUG}-{it.get('sku')}", tienda=TIENDA, nombre=(it.get("name") or "").strip(),
        precio=precio, antes=normal if normal > precio + 0.01 else None,
        url=f"https://{HOST}/{it.get('url_key', '')}{it.get('url_suffix') or '.html'}",
        imagen=(it.get("small_image") or {}).get("url"),
        categoria=" / ".join(c for c in cats[-2:] if c),
        disponible=it.get("stock_status") == "IN_STOCK", modelo=it.get("sku") or "")


def recolectar(tiempo_limite=420):
    inicio = time.monotonic()
    vistos = {}
    n, total = 1, 1
    while n <= total and time.monotonic() - inicio < tiempo_limite:
        data = _pagina(n)
        if not data:
            break
        total = (data.get("page_info") or {}).get("total_pages") or 1
        for it in data.get("items") or []:
            p = _producto(it)
            if p:
                vistos[p["id"]] = p
        n += 1
    return list(vistos.values())
