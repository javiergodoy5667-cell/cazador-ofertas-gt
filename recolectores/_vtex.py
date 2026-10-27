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

# Nombres de categoria/coleccion que indican ofertas (sin mayusculas ni tildes).
SECCIONES_OFERTA = ("oferta", "ofertas", "liquidacion", "outlet", "precios bajos",
                    "descuento", "hot sale", "promocion", "rebaja", "cyber",
                    "flash", "black", "precio especial", "remate", "promo")


def _seccion_de(texto):
    """Nombre de seccion si el texto (categoria o cluster) es de oferta."""
    import unicodedata
    t = unicodedata.normalize("NFKD", texto or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return any(k in t for k in SECCIONES_OFERTA)


def _seccion_cluster(p):
    """Devuelve el nombre del cluster de oferta del producto, o None."""
    clusters = p.get("productClusters") or {}
    for _cid, nombre in clusters.items():
        if _seccion_de(nombre):
            return nombre
    return None


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


def _producto(p, slug, tienda, host, prefijo, dominio_link=None):
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
        enlace = dominio_link or host
        return pid, _base.nuevo_producto(
            id_=f"{slug}-{pid}", tienda=tienda, nombre=p.get("productName", ""),
            precio=precio, antes=antes,
            url=f"https://{enlace}{prefijo}/{link_text}/p", imagen=img,
            categoria=categoria, disponible=bool(offer.get("IsAvailable")),
            fin_oferta=offer.get("PriceValidUntil"),
            ean=item.get("ean", ""),
            marca=p.get("brand", ""),
            modelo=p.get("productReference", "") or item.get("name", ""))
    except (KeyError, IndexError, TypeError):
        return None, None


def recolectar_vtex(slug, tienda, host, prefijo="", max_productos=6000,
                    tiempo_limite=420, prioridad=None, dominio_link=None):
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

    clusters_oferta = {}
    for cid, _nombre in raices:
        if time.monotonic() - inicio > tiempo_limite or len(vistos) >= max_productos:
            break
        seccion = _nombre if _seccion_de(_nombre) else None
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
                # colecciones (clusters) de oferta
                for ccid, cnombre in (p.get("productClusters") or {}).items():
                    if _seccion_de(cnombre):
                        clusters_oferta[ccid] = cnombre
                pid, prod = _producto(p, slug, tienda, host, prefijo, dominio_link)
                if pid is not None and pid not in vistos:
                    sec = seccion or _seccion_cluster(p)
                    if sec:
                        prod["seccion_oferta"] = sec
                    vistos[pid] = prod
            if len(data) < PASO:
                break  # ultima pagina de esta categoria

    # Recorrer las colecciones de oferta encontradas (hasta 3, 1 pagina cada una).
    for ccid, cnombre in list(clusters_oferta.items())[:3]:
        if time.monotonic() - inicio > tiempo_limite or len(vistos) >= max_productos:
            break
        url = (f"https://{host}/api/catalog_system/pub/products/search"
               f"?fq=productClusterIds:{ccid}&_from=0&_to={PASO - 1}")
        st3, _fu3, b3 = _base.get(url, host=host)
        if st3 not in (200, 206) or not b3:
            continue
        try:
            data3 = json.loads(b3)
        except Exception:
            continue
        if not isinstance(data3, list):
            continue
        for p in data3:
            pid, prod = _producto(p, slug, tienda, host, prefijo, dominio_link)
            if pid is not None and pid not in vistos:
                prod["seccion_oferta"] = cnombre
                vistos[pid] = prod
    return list(vistos.values())
