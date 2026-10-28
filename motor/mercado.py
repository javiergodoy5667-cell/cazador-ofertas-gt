# -*- coding: utf-8 -*-
"""
Comparacion entre tiendas (auditoria 10).
Para que dos productos sean "el mismo" deben cumplir TODO:
  a) mismo EAN,
  b) nombre compatible (misma marca o >=2 palabras clave en comun),
  c) mismo tamano/peso/unidades (si alguno lo declara).
Si algo falla, NO se comparan (evita Snack Mix vs Jamon con el mismo EAN).
"""
import re
import statistics
import unicodedata

STOP = {"de", "la", "el", "los", "las", "con", "para", "por", "del", "al", "y",
        "en", "un", "una", "sin", "pack", "paquete", "the", "and", "new"}

UNIDADES = {"ml": "ml", "mililitros": "ml", "g": "g", "gr": "g", "gramos": "g",
            "kg": "kg", "kilos": "kg", "kilo": "kg", "l": "l", "lt": "l",
            "litros": "l", "litro": "l", "oz": "oz", "onzas": "oz",
            "unidades": "u", "unidad": "u", "uds": "u", "ud": "u",
            "pzas": "u", "pza": "u", "piezas": "u", "pieza": "u"}


def _norm(texto):
    t = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _palabras(nombre):
    return {w for w in re.findall(r"[a-z0-9]+", _norm(nombre))
            if len(w) >= 3 and w not in STOP}


def _tamano(nombre):
    """(valor, unidad) normalizado; ('', '') si no declara tamano."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*"
                  r"(ml|mililitros|g|gr|gramos|kg|kilos?|l|lt|litros?|oz|onzas|"
                  r"unidades?|uds?|pzas?|piezas?)\b", _norm(nombre))
    if not m:
        return ("", "")
    val = m.group(1).replace(",", ".")
    return (val, UNIDADES.get(m.group(2), m.group(2)))


def compatible(p1, p2):
    """Misma marca o >=2 palabras clave en comun."""
    b1, b2 = _norm(p1.get("marca")), _norm(p2.get("marca"))
    if b1 and b2 and (b1 in b2 or b2 in b1):
        return True
    w1, w2 = _palabras(p1.get("nombre")), _palabras(p2.get("nombre"))
    if not w1 and not w2:
        return True   # sin nombres no se puede juzgar
    return len(w1 & w2) >= 2


def mismo_tamano(p1, p2):
    """Si AMBOS declaran tamano, deben coincidir. Si uno no lo declara, no se
    puede confirmar el tamano, pero el EAN + nombre ya identifican el producto."""
    v1, u1 = _tamano(p1.get("nombre"))
    v2, u2 = _tamano(p2.get("nombre"))
    if not v1 or not v2:
        return True
    return v1 == v2 and u1 == u2


def clave(prod):
    """EAN identico. Si no hay EAN, no se compara."""
    ean = prod.get("ean") or ""
    return ("ean", ean) if ean else None


def calcular(productos):
    """{id: {precio_mercado, mercado, antes_inflado, tiendas}} con EAN + nombre + tamano."""
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
                     if q["tienda"] != p["tienda"] and q.get("disponible", True)
                     and compatible(p, q) and mismo_tamano(p, q)]
            if not otros:
                continue
            precios = [q["precio_actual"] for q in otros]
            precio_mercado = statistics.median(precios)
            antes = p.get("precio_antes_tienda")
            inflado = bool(antes and antes > 1.15 * max(precios))
            mas_barato = min(otros, key=lambda q: q["precio_actual"])
            out[p["id"]] = {
                "precio_mercado": round(precio_mercado, 2),
                "mercado": [{"tienda": q["tienda"],
                             "precio": q["precio_actual"],
                             "url": q.get("url", "")} for q in otros],
                "antes_inflado": inflado,
                "por_ean": True,
                "tiendas": len({q["tienda"] for q in otros}),
                "mas_barato_que": {"tienda": mas_barato["tienda"],
                                   "precio": mas_barato["precio_actual"]},
            }
    return out
