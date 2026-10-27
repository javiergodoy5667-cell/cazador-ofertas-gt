# -*- coding: utf-8 -*-
"""Smoke: recolecta una muestra y mide % de categoria 'Otros'."""
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
                                 prefijo="", tiempo_limite=45, max_productos=4000)
    print(f"Muestra Cemaco: {len(prod)} productos")
    dist = Counter()
    otros_rutas = Counter()
    for p in prod:
        c = categorias.clasificar(p.get("categoria", ""), p.get("nombre", ""))
        dist[c] += 1
        if c == "📦 Otros":
            otros_rutas[p.get("categoria", "")[:60]] += 1
    total = len(prod)
    otros = dist.get("📦 Otros", 0)
    print(f"% Otros: {otros / total * 100:.1f}%")
    print("\nDistribución:")
    for c, n in dist.most_common():
        print(f"  {c:<30} {n}")
    print("\nTop rutas crudas que cayeron en Otros:")
    for r, n in otros_rutas.most_common(20):
        print(f"  {n:>4}  {r}")
