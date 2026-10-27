# -*- coding: utf-8 -*-
"""Verificar si fin_oferta (PriceValidUntil) de VTEX es relampago real o default."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from recolectores import _base


def fin_de(host, terminos, prefijo=""):
    fechas = Counter()
    total = 0
    for t in terminos:
        url = (f"https://{host}/api/catalog_system/pub/products/search"
               f"?ft={t}&_from=0&_to=49")
        st, _fu, body = _base.get(url, host=host)
        if st not in (200, 206) or not body:
            continue
        try:
            data = json.loads(body)
        except Exception:
            continue
        for p in data:
            total += 1
            try:
                fin = p["items"][0]["sellers"][0]["commertialOffer"].get(
                    "PriceValidUntil")
            except Exception:
                fin = None
            fechas[str(fin)] += 1
    return total, fechas


for host, nombre in [("www.siman.com", "Siman"), ("www.cemaco.com", "Cemaco"),
                     ("www.elektra.com.gt", "Elektra")]:
    total, fechas = fin_de(host, ["casco", "televisor", "celular", "refrigeradora"])
    top = fechas.most_common(5)
    print(f"\n{nombre}: {total} productos, {len(fechas)} fechas fin_oferta distintas")
    for f, n in top:
        print(f"  {f}  ->  {n}")
