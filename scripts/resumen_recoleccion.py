# -*- coding: utf-8 -*-
"""Resumen de la ultima recoleccion: conteo, validez y top descuentos."""
import glob
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    files = sorted(BASE.glob("data/recoleccion_*.json"))
    if not files:
        print("No hay recoleccion guardada en data/")
        return
    data = json.loads(files[-1].read_text(encoding="utf-8"))
    print(f"Archivo: {files[-1].name}")
    print(f"Productos: {len(data)}")
    por_tienda = {}
    for p in data:
        por_tienda[p["tienda"]] = por_tienda.get(p["tienda"], 0) + 1
    print("Por tienda:", por_tienda)
    con_antes = [p for p in data if p.get("precio_antes_tienda")
                 and p["precio_antes_tienda"] > p["precio_actual"]]
    print(f"Con descuento real (antes > actual): {len(con_antes)}")
    malos = [p for p in data if not p.get("precio_actual")
             or p["precio_actual"] <= 0]
    print(f"Precios invalidos: {len(malos)}")
    con_antes.sort(key=lambda p: (p["precio_antes_tienda"] - p["precio_actual"])
                   / p["precio_antes_tienda"], reverse=True)
    print("\nTop 5 descuentos reales:")
    for p in con_antes[:5]:
        d = (p["precio_antes_tienda"] - p["precio_actual"]) / p["precio_antes_tienda"] * 100
        print(f"  -{d:4.0f}%  {p['tienda']:<12} Q{p['precio_actual']:>9.2f} "
              f"(antes Q{p['precio_antes_tienda']:.2f})  {p['nombre'][:45]}")


if __name__ == "__main__":
    main()
