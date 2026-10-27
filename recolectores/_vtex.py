# -*- coding: utf-8 -*-
"""
Recolector generico para tiendas VTEX con cobertura amplia.
1. Descarga el arbol de categorias (/api/catalog_system/pub/category/tree/3).
2. Toma las categorias RAIZ y pagina cada una con fq=C:/{id}/ de 50 en 50
   hasta _from=2500 (limite de la API).
3. Deduplica por productId y se detiene por tiempo (por defecto 7 min) o por
   maximo de productos.
"""
import json
import time

from . import _base

MAX_FROM = 2500   # _from maximo que permite la API publica de VTEX
PASO = 50

# Nombres de categoria que indican seccion de ofertas/liquidacion.
SECCIONES_OFERTA = ("oferta", "ofertas", "liquidacion", "liquidación", "outlet",
                    "precios bajos", "descuento", "hot sale", "promocion",
                    "promoción", "rebaja", "cyber")


def _raices(tree):
    out = []
    for n in tree:
        if isinstance(n, dict) and n.get("id") is not None:
            out.append((n["id"], n.get("name", "")))
    return out


def _ordenar_por_prioridad(raices, prioridad):
    """Pone primero las raices cuya categoria unificada esta en `prioridad`
    (categorias de alerta), para que el tope no corte antes de visitarlas."""
    if not prioridad:
        return raices
    try:
        from motor.categorias import clasificar
    except Exception:
        return raices
    prio = set(prioridad)
    primeras = [r for r in raices if clasificar("", r[1]) in prio]
    resto = [r for r in raices if r not in primeras]
    return primeras + resto


def _producto(p, slug, tienda, host, prefijo):
    try:
        pid = p.get("productId")
        item = p["items"][0]
        seller = item["sellers"][0]
        offer = seller.get("commertialOffer", {})
        precio = _base.limpiar_precio(offer.get("Price"))
        antes = _base.limpiar_precio(offer.get("ListPrice"))
        if precio is None or precio <= 0:
            return None, None
        link_text = p.get("linkText", "")
        img = item["images"][0]["imageUrl"] if item.get("images") else None
        categoria = (p.get("categories") or [""])[0]
        return pid, _base.nuevo_producto(
            id_=f"{slug}-{pid}", tienda=tienda, nombre=p.get("productName", ""),
            precio=precio, antes=antes,
            url=f"https://{host}{prefijo}/{link_text}/p", imagen=img,
            categoria=categoria, disponible=bool(offer.get("IsAvailable")),
            fin_oferta=offer.get("PriceValidUntil"))
    except (KeyError, IndexError, TypeError):
        return None, None


def recolectar_vtex(slug, tienda, host, prefijo="", max_productos=6000,
                    tiempo_limite=420, prioridad=None):
    inicio = time.monotonic()
    vistos = {}
    if prioridad is None:
        try:
            from motor.config import cargar
            prioridad = cargar().get("categorias_alerta", [])
        except Exception:
            prioridad = []

    st, _fu, body = _base.get(
        f"https://{host}/api/catalog_system/pub/category/tree/3", host=host)
    raices = []
    if st in (200, 206) and body:
        try:
            raices = _raices(json.loads(body))
        except Exception:
            raices = []
    raices = _ordenar_por_prioridad(raices, prioridad)

    for cid, _nombre in raices:
        if time.monotonic() - inicio > tiempo_limite or len(vistos) >= max_productos:
            break
        nombre_root = (_nombre or "").lower()
        seccion = _nombre if any(k in nombre_root for k in SECCIONES_OFERTA) else None
        for _from in range(0, MAX_FROM, PASO):
            if time.monotonic() - inicio > tiempo_limite or len(vistos) >= max_productos:
                break
            url = (f"https://{host}/api/catalog_system/pub/products/search"
                   f"?fq=C:/{cid}/&_from={_from}&_to={_from + PASO - 1}")
            st2, _fu2, b2 = _base.get(url, host=host)
            if st2 not in (200, 206) or not b2:
                break
            try:
                data = json.loads(b2)
            except Exception:
                break
            if not isinstance(data, list) or not data:
                break
            for p in data:
                pid, prod = _producto(p, slug, tienda, host, prefijo)
                if pid is not None and pid not in vistos:
                    if seccion:
                        prod["seccion_oferta"] = seccion
                    vistos[pid] = prod
            if len(data) < PASO:
                break  # ultima pagina de esta categoria
    return list(vistos.values())
