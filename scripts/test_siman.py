# -*- coding: utf-8 -*-
"""Prueba: 3 productos de Siman Guatemala en quetzales + link GT."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from recolectores import _vtex

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = _vtex.recolectar_vtex("siman", "Simán",
                              "simanguatemala.vtexcommercestable.com.br",
                              prefijo="", tiempo_limite=30, max_productos=300,
                              dominio_link="gt.siman.com")
    print(f"Siman GT: {len(r)} productos")
    for p in r[:3]:
        print(f"  {p['nombre'][:45]:<45} | Q{p['precio_actual']:>8.2f} | {p['url'][:70]}")
