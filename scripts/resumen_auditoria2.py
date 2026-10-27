# -*- coding: utf-8 -*-
"""Resumen de la auditoria 2: ofertas por categoria, relampagos, % Otros."""
import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ofertas = json.loads((BASE / "web" / "ofertas.json").read_text(encoding="utf-8"))
    total = len(ofertas)
    por_cat = Counter(o.get("categoria", "📦 Otros") for o in ofertas)
    relampagos = sum(1 for o in ofertas if o.get("relampago"))
    otros = por_cat.get("📦 Otros", 0)
    print(f"Ofertas totales: {total}")
    print(f"Relámpagos reales (etiqueta): {relampagos}")
    print(f"% en Otros: {otros / total * 100:.1f}%" if total else "0 productos")
    print("\nOfertas por categoría:")
    for c, n in por_cat.most_common():
        print(f"  {c:<30} {n}")


if __name__ == "__main__":
    main()
