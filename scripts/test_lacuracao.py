# -*- coding: utf-8 -*-
"""Diagnostico La Curacao: descubrimiento de categorias + parseo de una pagina."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from recolectores import _base, lacuracao

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    st, fu, html = _base.get(lacuracao.BASE + "/", host=lacuracao.HOST)
    print(f"home: {st} len={len(html)}")
    cats = lacuracao._descubrir_categorias()
    print(f"categorias descubiertas: {len(cats)} -> {cats[:8]}")
    if cats:
        st, fu, body = _base.get(f"{lacuracao.BASE}/c/{cats[0]}", host=lacuracao.HOST)
        print(f"categoria {cats[0]}: {st} len={len(body)}")
        prods = lacuracao._extraer_productos(body)
        print(f"productos en la categoria: {len(prods)}")
        if prods:
            print("ejemplo:", prods[0]["nombre"][:50], "Q", prods[0]["precio_actual"])
