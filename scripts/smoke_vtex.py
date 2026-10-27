# -*- coding: utf-8 -*-
"""Smoke test del recolector VTEX con limite corto de tiempo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recolectores import _vtex

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = _vtex.recolectar_vtex("cemaco", "Cemaco", "www.cemaco.com",
                              prefijo="", tiempo_limite=40, max_productos=6000)
    print(f"Cemaco (40s): {len(r)} productos")
    if r:
        x = r[0]
        print("ejemplo:", x["nombre"][:60], "| Q", x["precio_actual"])
