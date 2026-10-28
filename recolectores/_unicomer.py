# -*- coding: utf-8 -*-
"""
Base de Max y Tecnofacil (misma plataforma: Next.js sobre Magento).
Cada pagina de categoria trae en <script id="__NEXT_DATA__"> la lista
props.pageProps.productsList (12 por pagina) con sku, slug, title,
eanCode, regularPrice, salesPrice y status. Las categorias salen de
/server-sitemap.xml; se leen solo las "hojas" (sin subcategorias) para no
repetir productos, y primero las categorias que interesan al usuario.
robots.txt prohibe URLs con "?" (Disallow: /*?), asi que solo se lee la
pagina 1 de cada hoja (sin ?page=N). Si no caben todas, el resto rota por hora.
"""
import datetime as dt
import json
import re
import time

from . import _base

# Orden de lectura: ofertas y categorias de alerta primero.
PRIORIDAD = ["ofertas-web", "celulares", "tv-y-video", "electronicos",
             "linea-blanca", "videojuegos", "audio", "mejora-del-hogar",
             "movilidad", "hogar"]
EXCLUIR = ["guias-de-compra"]
HOJAS_POR_CORRIDA = 400


def _hojas(host):
    st, _fu, xml = _base.get(f"https://{host}/server-sitemap.xml", host=host)
    if st != 200 or not xml:
        return []
    rutas = []
    for u in re.findall(r"<loc>([^<]+)</loc>", xml):
        ruta = re.sub(r"^https?://[^/]+/", "", u.strip()).strip("/")
        if ruta and not any(ruta.startswith(e) for e in EXCLUIR):
            rutas.append(ruta)
    rutas = list(dict.fromkeys(rutas))
    hojas = [r for r in rutas if not any(o.startswith(r + "/") for o in rutas)]

    def orden(r):
        raiz = r.split("/")[0]
        return PRIORIDAD.index(raiz) if raiz in PRIORIDAD else len(PRIORIDAD)
    return sorted(hojas, key=orden)


def _lista(html):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return 0, []
    try:
        pp = json.loads(m.group(1))["props"]["pageProps"]
    except Exception:
        return 0, []
    return int(pp.get("totalCount") or 0), pp.get("productsList") or []


def _valor(p):
    return _base.limpiar_precio((p or {}).get("value")) if isinstance(p, dict) else None


def _producto(it, slug_tienda, tienda, host, ruta):
    regular = _valor(it.get("regularPrice"))
    venta = _valor(it.get("salesPrice"))
    precio = venta or regular
    if not precio or precio <= 0:
        return None
    moneda = (it.get("salesPrice") or it.get("regularPrice") or {}).get("currency")
    if moneda and moneda != "GTQ":
        return None
    sku = it.get("sku") or ""
    marca = it.get("brand") or {}
    return _base.nuevo_producto(
        id_=f"{slug_tienda}-{sku}", tienda=tienda, nombre=it.get("title", ""),
        precio=precio, antes=regular if venta and regular and regular > venta else None,
        url=f"https://{host}/{it.get('slug', '')}",
        imagen=(it.get("thumbnailImage") or {}).get("url"),
        categoria=ruta, disponible=it.get("status") == "IN_STOCK",
        ean=it.get("eanCode") or "",
        marca=marca.get("title", "") if isinstance(marca, dict) else "",
        modelo=sku)


def _turno(hojas):
    """Las primeras (prioritarias) siempre; el resto rota por hora."""
    if len(hojas) <= HOJAS_POR_CORRIDA:
        return hojas
    fijas = HOJAS_POR_CORRIDA // 2
    prio, resto = hojas[:fijas], hojas[fijas:]
    cupo = HOJAS_POR_CORRIDA - fijas
    ini = (dt.datetime.utcnow().hour * cupo) % len(resto)
    return prio + (resto + resto)[ini:ini + cupo]


def recolectar_unicomer(slug_tienda, tienda, host, tiempo_limite=420):
    inicio = time.monotonic()
    vistos = {}
    for ruta in _turno(_hojas(host)):
        if time.monotonic() - inicio > tiempo_limite:
            break
        st, _fu, html = _base.get(f"https://{host}/{ruta}", host=host)
        if st != 200 or not html:
            continue
        _total, items = _lista(html)
        for it in items:
            p = _producto(it, slug_tienda, tienda, host, ruta)
            if p and p["id"] not in vistos:
                vistos[p["id"]] = p
    return list(vistos.values())
