# -*- coding: utf-8 -*-
"""
Comparacion entre tiendas: precio de mercado real.
Empareja por EAN (codigo de barras) y, si no hay, por marca + modelo exacto.
Calcula la mediana de precios ACTUALES de las otras tiendas (sin la propia ni
agotados) y marca "antes_inflado" si el precio "antes" de la tienda supera en
>15% al precio mas alto de las otras tiendas.
"""
import statistics


def _norm(s):
    return "".join(c for c in (s or "").lower() if c.isalnum())


def clave(prod):
    """Clave de emparejamiento entre tiendas, o None si no se puede."""
    ean = prod.get("ean") or ""
    if ean:
        return ("ean", ean)
    marca = _norm(prod.get("marca"))
    modelo = _norm(prod.get("modelo"))
    if marca and modelo and len(modelo) >= 4:
        return ("mm", marca + "|" + modelo)
    return None


def calcular(productos):
    """Devuelve {id: {precio_mercado, mercado:[{tienda,precio,url}], antes_inflado}}."""
    por_clave = {}
    for p in productos:
        k = clave(p)
        if k:
            por_clave.setdefault(k, []).append(p)

    out = {}
    for _k, lista in por_clave.items():
        tiendas = {p["tienda"] for p in lista}
        if len(tiendas) < 2:
            continue
        for p in lista:
            otros = [q for q in lista
                     if q["tienda"] != p["tienda"] and q.get("disponible", True)]
            if not otros:
                continue
            precios = [q["precio_actual"] for q in otros]
            precio_mercado = statistics.median(precios)
            antes = p.get("precio_antes_tienda")
            inflado = bool(antes and antes > 1.15 * max(precios))
            out[p["id"]] = {
                "precio_mercado": round(precio_mercado, 2),
                "mercado": [{"tienda": q["tienda"],
                             "precio": q["precio_actual"],
                             "url": q.get("url", "")} for q in otros],
                "antes_inflado": inflado,
            }
    return out
