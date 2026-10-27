# -*- coding: utf-8 -*-
"""Resumen auditoria 3: categorias de alerta, secciones de oferta, sin verificar."""
import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ALERTA = ["🔧 Ferretería y herramientas", "🔌 Eléctrico", "📱 Celulares y tablets",
          "📺 TV y audio", "💻 Computación y videojuegos", "🧊 Línea blanca",
          "🍳 Electrodomésticos de cocina", "🚗 Automotriz"]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ofertas = json.loads((BASE / "web" / "ofertas.json").read_text(encoding="utf-8"))
    total = len(ofertas)
    por_cat = Counter(o.get("categoria", "📦 Otros") for o in ofertas)
    secciones = Counter(o.get("seccion_oferta", "") for o in ofertas if o.get("seccion_oferta"))
    sin_verif = [o for o in ofertas if o.get("sin_historial")
                 and (o.get("precio_antes_tienda") or 0) > 0
                 and (o["precio_antes_tienda"] - o["precio_actual"]) / o["precio_antes_tienda"] >= 0.5]
    print(f"Ofertas totales: {total}")
    print(f"Sin verificar (antes>=50%): {len(sin_verif)}")
    print("\nCategorias de ALERTA:")
    for c in ALERTA:
        print(f"  {c:<32} {por_cat.get(c, 0)}")
    print("\nTodas las categorias:")
    for c, n in por_cat.most_common():
        print(f"  {c:<32} {n}")
    print("\nSecciones de oferta encontradas:")
    for s, n in secciones.most_common():
        print(f"  {s[:40]:<40} {n} productos")
    if not secciones:
        print("  (ninguna)")


if __name__ == "__main__":
    main()
