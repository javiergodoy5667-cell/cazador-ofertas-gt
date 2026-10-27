# -*- coding: utf-8 -*-
"""Resumen auditoria 7: Siman GT, ofertas por tienda/categoria, top 10."""
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
    estado = json.loads((BASE / "web" / "estado.json").read_text(encoding="utf-8"))
    resumen = json.loads((BASE / "web" / "ofertas-resumen.json").read_text(encoding="utf-8"))

    siman = [r for r in resumen if r["t"] == "Simán"]
    print(f"Siman GT: {len(siman)} ofertas | precios: "
          f"{[round(r['p'], 1) for r in siman[:6]]}")

    print(f"\nOfertas por tienda: {dict(Counter(r['t'] for r in resumen))}")
    por_cat = Counter(r["c"] for r in resumen)
    print("\nOfertas por categoria de ALERTA:")
    for c in ALERTA:
        print(f"  {c:<32} {por_cat.get(c, 0)}")
    print(f"\nMarcadas 'revisar': {sum(1 for r in resumen if r.get('rev'))}")
    print(f"Con comparacion (mercado): {sum(1 for r in resumen if r.get('m'))}")
    print(f"Con EAN en el estado: {estado.get('con_ean')}")

    print("\n--- Top 10 por descuento ---")
    top = sorted(resumen, key=lambda r: -r["d"])[:10]
    for r in top:
        print(f"{r['t']:<12} | {r['n'][:42]:<42} | Q{r['p']:>8.1f} | "
              f"-{round(r['d']*100):>3}% | ref Q{r['dr']:>8.1f} | {r['u'][:70]}")
        for m in r.get("m", [])[:3]:
            print(f"      vs {m['t']:<12} Q{m['p']:>8.1f}  {m['u'][:70]}")


if __name__ == "__main__":
    main()
