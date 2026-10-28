# -*- coding: utf-8 -*-
"""
Comparacion entre tiendas — SOLO por EAN (auditoria 9).
Se apago el emparejamiento por codigo de modelo y por marca+modelo porque juntaba
productos distintos (microondas vs estufa, protector vs iPhone...).
Si no hay EAN igual, NO se compara.
"""
import statistics


def clave(prod):
    """Unica clave valida: EAN identico. Si no hay EAN, no se compara."""
    ean = prod.get("ean") or ""
    return ("ean", ean) if ean else None


def calcular(productos):
    """{id: {precio_mercado, mercado, antes_inflado, tiendas}} solo con EAN igual."""
    por_clave = {}
    for p in productos:
        k = clave(p)
        if k:
            por_clave.setdefault(k, []).append(p)

    out = {}
    for _k, lista in por_clave.items():
        if len({p["tienda"] for p in lista}) < 2:
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
                "por_ean": True,
                "tiendas": len({q["tienda"] for q in otros}),
            }
    return out
