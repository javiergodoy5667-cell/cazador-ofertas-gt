# -*- coding: utf-8 -*-
"""Resumen auditoria 4/5: EAN, coincidencias, inflados, verificadas, peso."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    estado = json.loads((BASE / "web" / "estado.json").read_text(encoding="utf-8"))
    resumen = json.loads((BASE / "web" / "ofertas-resumen.json").read_text(encoding="utf-8"))

    total = estado.get("productos_leidos", 0)
    con_ean = estado.get("con_ean", {})
    print(f"Productos leidos: {total}")
    print("% con EAN por tienda:")
    for t, n in sorted(con_ean.items(), key=lambda x: -x[1]):
        print(f"  {t:<14} {n:>6}")
    print(f"  (total con EAN: {sum(con_ean.values())})")
    print(f"Coincidencias en 2+ tiendas: {estado.get('coincidencias', 0)}")
    print(f"Antes inflados detectados: {estado.get('antes_inflado', 0)}")
    print("\nEjemplos de 'antes' inflado:")
    for e in estado.get("inflado_ejemplos", []):
        print(f"  {e['tienda']} | antes Q{e['antes']:,.0f} | precio Q{e['precio']:,.0f} "
              f"| max otro Q{e['max_otro']:,.0f} | {e['nombre'][:45]}")
        print(f"      {e['url'][:110]}")
    verif = len(resumen)
    con_mercado = sum(1 for r in resumen if r.get("m"))
    print(f"\nOfertas verificadas: {verif} (con comparacion: {con_mercado}, "
          f"por historial: {verif - con_mercado})")
    for f in ("ofertas-resumen.json", "estado.json", "precios.json"):
        p = BASE / "web" / f
        print(f"  {f:<22} {p.stat().st_size/1024:.1f} KB")
    print(f"  primera carga (resumen+estado+precios): "
          f"{sum((BASE/'web'/f).stat().st_size for f in ('ofertas-resumen.json','estado.json','precios.json'))/1024:.1f} KB")


if __name__ == "__main__":
    main()
