# -*- coding: utf-8 -*-
"""Smoke test de La Curacao."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recolectores import lacuracao

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = lacuracao.recolectar()
    print(f"La Curacao: {len(r)} productos")
    if r:
        x = r[0]
        print("ejemplo:", x["nombre"][:60], "| Q", x["precio_actual"], "|", x["url"][:60])
