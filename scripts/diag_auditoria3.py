# -*- coding: utf-8 -*-
"""Diagnostico auditoria 3: orden de raices + clasificacion de productos reales."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from recolectores import _base
from motor import categorias

HOST = "www.cemaco.com"
CLAVES = ["taladro", "sierra", "cable", "breaker", "foco", "extension",
          "bateria", "aceite", "llanta"]


def raices():
    st, _fu, body = _base.get(
        f"https://{HOST}/api/catalog_system/pub/category/tree/3", host=HOST)
    tree = json.loads(body)
    out = [(n["id"], n.get("name", "")) for n in tree if isinstance(n, dict)]
    return out


print("=== Raices de Cemaco (orden del arbol) y su clasificacion ===")
for i, (cid, nombre) in enumerate(raices()):
    print(f"{i:>2}  id={cid:<6} {nombre:<35} -> {categorias.clasificar('', nombre)}")

print("\n=== 30 productos reales por palabra clave ===")
vistos = 0
for clave in CLAVES:
    url = (f"https://{HOST}/api/catalog_system/pub/products/search"
           f"?ft={clave}&_from=0&_to=3")
    st, _fu, body = _base.get(url, host=HOST)
    if st not in (200, 206) or not body:
        continue
    try:
        data = json.loads(body)
    except Exception:
        continue
    for p in data[:4]:
        ruta = (p.get("categories") or [""])[0]
        nombre = p.get("productName", "")
        cat = categorias.clasificar(ruta, nombre)
        print(f"  [{clave}] {nombre[:48]:<48} | ruta={ruta[:35]:<35} -> {cat}")
        vistos += 1
        if vistos >= 30:
            break
    if vistos >= 30:
        break
