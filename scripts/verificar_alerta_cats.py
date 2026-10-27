# -*- coding: utf-8 -*-
"""Verifica que el reordenamiento lea primero las categorias de alerta."""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from recolectores import _vtex
from motor import categorias

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    prod = _vtex.recolectar_vtex("cemaco", "Cemaco", "www.cemaco.com",
                                 prefijo="", tiempo_limite=90, max_productos=6000)
    print(f"Cemaco: {len(prod)} productos leidos en 90s")
    dist = Counter(categorias.clasificar(p.get("categoria", ""), p.get("nombre", ""))
                   for p in prod)
    print("\nProductos leidos por categoria:")
    for c, n in dist.most_common():
        print(f"  {c:<32} {n}")
