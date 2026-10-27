# -*- coding: utf-8 -*-
"""
Recolector generico para tiendas VTEX.
Usa el API publico de catalogo: /api/catalog_system/pub/products/search
Devuelve productos con Price (venta) y ListPrice (precio "antes").
"""
import json

from . import _base


def recolectar_vtex(slug, tienda, host, prefijo="", terminos=None,
                    max_productos=200, por_pagina=49):
    terminos = terminos or [
        "televisor", "laptop", "celular", "refrigeradora", "lavadora",
        "zapatos", "taladro", "cocina", "audifonos", "moto", "colchon",
        "licuadora", "microondas", "tablet", "impresora", "bicicleta",
        "horno", "estufa", "ventilador", "bateria", "smartwatch", "camara",
    ]
    vistos = {}
    for t in terminos:
        if len(vistos) >= max_productos:
            break
        url = (f"https://{host}/api/catalog_system/pub/products/search"
               f"?ft={t}&_from=0&_to={por_pagina}")
        status, _fu, body = _base.get(url, host=host)
        if status not in (200, 206) or not body:
            continue
        try:
            data = json.loads(body)
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for p in data:
            if len(vistos) >= max_productos:
                break
            try:
                pid = p.get("productId")
                if pid in vistos:
                    continue
                item = p["items"][0]
                seller = item["sellers"][0]
                offer = seller.get("commertialOffer", {})
                precio = _base.limpiar_precio(offer.get("Price"))
                antes = _base.limpiar_precio(offer.get("ListPrice"))
                if precio is None or precio <= 0:
                    continue
                link_text = p.get("linkText", "")
                img = (item["images"][0]["imageUrl"] if item.get("images") else None)
                categoria = (p.get("categories") or [""])[0]
                fin = offer.get("PriceValidUntil")
                vistos[pid] = _base.nuevo_producto(
                    id_=f"{slug}-{pid}", tienda=tienda,
                    nombre=p.get("productName", ""),
                    precio=precio, antes=antes,
                    url=f"https://{host}{prefijo}/{link_text}/p",
                    imagen=img, categoria=categoria,
                    disponible=bool(offer.get("IsAvailable")),
                    fin_oferta=fin)
            except (KeyError, IndexError, TypeError):
                continue
    return list(vistos.values())
