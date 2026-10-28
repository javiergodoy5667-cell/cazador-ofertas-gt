# -*- coding: utf-8 -*-
"""
Base de tiendas Shopify: /products.json?limit=250&page=N (catalogo publico).
price = precio actual; compare_at_price = precio "antes" de la tienda.
"""
import json
import time

from . import _base


def recolectar_shopify(slug_tienda, tienda, host, tiempo_limite=300, max_paginas=40):
    inicio = time.monotonic()
    vistos = {}
    for pagina in range(1, max_paginas + 1):
        if time.monotonic() - inicio > tiempo_limite:
            break
        st, _fu, txt = _base.get(
            f"https://{host}/products.json?limit=250&page={pagina}", host=host)
        if st != 200 or not txt:
            break
        try:
            productos = json.loads(txt).get("products") or []
        except Exception:
            break
        if not productos:
            break
        for p in productos:
            vs = p.get("variants") or []
            if not vs:
                continue
            v = vs[0]
            precio = _base.limpiar_precio(v.get("price"))
            if not precio or precio <= 0:
                continue
            antes = _base.limpiar_precio(v.get("compare_at_price"))
            imgs = p.get("images") or []
            pid = f"{slug_tienda}-{p.get('id')}"
            vistos[pid] = _base.nuevo_producto(
                id_=pid, tienda=tienda, nombre=p.get("title", ""),
                precio=precio, antes=antes if antes and antes > precio else None,
                url=f"https://{host}/products/{p.get('handle', '')}",
                imagen=imgs[0].get("src") if imgs else None,
                categoria=p.get("product_type") or "",
                disponible=bool(v.get("available")),
                ean=v.get("barcode") or "", marca=p.get("vendor") or "",
                modelo=v.get("sku") or "")
    return list(vistos.values())
