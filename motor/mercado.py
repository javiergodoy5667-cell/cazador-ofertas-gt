# -*- coding: utf-8 -*-
"""
Comparacion entre tiendas. Empareja por EAN; si no hay, exige marca + modelo
+ TAMANO/PESO (ml, g, L, kg) para evitar comparaciones falsas (lechuga, aceite
de otro tamano...). Devuelve precio_mercado, por_ean y cuantas tiendas confirman.
"""
import re
import statistics

UNIDADES = {"ml": "ml", "mililitros": "ml", "g": "g", "gr": "g", "gramos": "g",
            "kg": "kg", "kilos": "kg", "kilo": "kg", "l": "l", "lt": "l",
            "litros": "l", "litro": "l", "oz": "oz", "onzas": "oz"}


def _norm(s):
    return "".join(c for c in (s or "").lower() if c.isalnum())


def _tamano(nombre):
    """Extrae tamano/peso normalizado del nombre (ej. '1.5l', '500ml', '2kg')."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(ml|mililitros|g|gr|gramos|kg|kilos?|l|lt|litros?|oz|onzas)\b",
                  (nombre or "").lower())
    if not m:
        return ""
    val = m.group(1).replace(",", ".")
    return val + UNIDADES.get(m.group(2), m.group(2))


def clave(prod):
    """Clave de emparejamiento, o None si no es fiable."""
    ean = prod.get("ean") or ""
    if ean:
        return ("ean", ean)
    marca = _norm(prod.get("marca"))
    modelo = _norm(prod.get("modelo"))
    tam = _tamano(prod.get("nombre"))
    if marca and modelo and len(modelo) >= 4:
        # sin EAN: marca + modelo + tamano exacto
        return ("mm", marca + "|" + modelo + "|" + tam)
    return None


def calcular(productos):
    """{id: {precio_mercado, mercado, antes_inflado, por_ean, tiendas}}."""
    por_clave = {}
    for p in productos:
        k = clave(p)
        if k:
            por_clave.setdefault(k, []).append(p)

    out = {}
    for k, lista in por_clave.items():
        tiendas = {p["tienda"] for p in lista}
        if len(tiendas) < 2:
            continue
        por_ean = (k[0] == "ean")
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
                "por_ean": por_ean,
                "tiendas": len({q["tienda"] for q in otros}),
            }
    return out
