# -*- coding: utf-8 -*-
"""
Clasificador de categorias unificadas.
Lee config/categorias.yml. Clasifica PRIMERO por la ruta de categoria de la
tienda y, si no alcanza, por el nombre del producto. Devuelve "📦 Otros" si
no coincide nada.
"""
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RUTA = BASE / "config" / "categorias.yml"
OTROS = "📦 Otros"

_cache = None

# Rutas que NO describen el producto (mesa de regalos, sin categorizar, etc.):
# si la ruta las contiene, se clasifica solo por el nombre.
RUTAS_IGNORAR = ("mesa de regalos", "sin categorizar", "catalogo completo",
                 "institucional", "servicios", "nivel sin categorizar")


def _normalizar(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def cargar():
    global _cache
    if _cache is not None:
        return _cache
    cats = []
    for linea in RUTA.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea.startswith("- "):
            continue
        body = linea[2:].strip()
        if ":" not in body:
            continue
        nombre, claves = body.split(":", 1)
        claves = [_normalizar(c.strip()) for c in claves.split(",") if c.strip()]
        cats.append((nombre.strip(), claves))
    _cache = cats
    return cats


def clasificar(ruta_tienda, nombre):
    """Devuelve la categoria unificada (con emoji)."""
    cats = cargar()
    ruta = _normalizar(ruta_tienda)
    nom = _normalizar(nombre)

    def mejor_en(texto):
        mejor, mejor_len = None, 0
        for cat, claves in cats:
            for c in claves:
                if c and c in texto and len(c) > mejor_len:
                    mejor, mejor_len = cat, len(c)
        return mejor

    r = mejor_en(ruta)          # 1. por ruta (prioridad), salvo rutas genericas
    if any(x in ruta for x in RUTAS_IGNORAR):
        r = None
    if r:
        return r
    return mejor_en(nom) or OTROS   # 2. por nombre


def lista():
    """Devuelve la lista ordenada de nombres de categoria."""
    return [n for n, _ in cargar()]
