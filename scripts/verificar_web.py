# -*- coding: utf-8 -*-
"""Verifica que la pagina publicada en GitHub Pages responda y sirva datos."""
import json
import urllib.request

BASE = "https://javiergodoy5667-cell.github.io/cazador-ofertas-gt/"

for u in (BASE, BASE + "ofertas.json", BASE + "manifest.json",
          BASE + "precios.json", BASE + "service-worker.js"):
    try:
        r = urllib.request.urlopen(u, timeout=25)
        b = r.read()
        print(f"{r.status:>3}  {len(b):>7} bytes  {u}")
    except Exception as e:
        print(f"ERR  {u}  {type(e).__name__}: {e}")

r = urllib.request.urlopen(BASE + "ofertas.json", timeout=25)
d = json.loads(r.read().decode("utf-8"))
print("Ofertas servidas en la web:", len(d))
