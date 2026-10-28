# -*- coding: utf-8 -*-
"""
Filtros de exclusion (auditoria 9). Estos productos NO son ofertas aunque el
precio parezca bueno: son anticipos, accesorios, combos, usados, etc.
"""
import re
import unicodedata

# Palabras/frases que descartan el producto.
EXCLUIR = (
    "reserva", "aparta", "apartado", "preventa", "pre-venta", "anticipo",
    "enganche", "cuota", "abono",
    "para iphone", "para samsung", "para xiaomi", "para huawei", "compatible con",
    "protector", "funda", "case", "mica", "cargador", "cable",
    "combo", "kit", "paquete de", "pack de",
    "reacondicionado", "usado", "open box", "exhibicion", "demo",
    "refurbished", "refurb",
)

# Palabras que solo cuentan como exclusion si aparecen como palabra completa.
_WORD = ("case", "kit", "pack", "mica", "demo", "usado")


def _norm(texto):
    t = unicodedata.normalize("NFKD", texto or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower()


def excluido(nombre):
    """True si el nombre del producto cae en una exclusion (no es oferta real)."""
    n = _norm(nombre)
    for p in EXCLUIR:
        if " " in p:
            if p in n:
                return True
        else:
            if re.search(r"\b" + re.escape(p) + r"\b", n):
                return True
    return False
