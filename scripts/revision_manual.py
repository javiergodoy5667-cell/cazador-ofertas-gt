# -*- coding: utf-8 -*-
"""Revision manual (auditoria 10): tablas por categoria/tienda + 10 top + 30 al azar."""
import json
import random
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = json.loads((BASE / "web" / "ofertas-resumen.json").read_text(encoding="utf-8"))
    estado = json.loads((BASE / "web" / "estado.json").read_text(encoding="utf-8"))

    print(f"Total ofertas: {len(r)}")
    print("\n== Por categoria ==")
    for c, n in Counter(x["c"] for x in r).most_common():
        print(f"  {c:<34} {n:>4}  ({n*100//max(len(r),1)}%)")
    print("\n== Por tienda ==")
    for t, n in Counter(x["t"] for x in r).most_common():
        print(f"  {t:<16} {n:>4}")
    print("\n== Por nivel ==")
    for lv, n in Counter(x["lv"] for x in r).most_common():
        print(f"  {lv:<12} {n:>4}")
    print("\n== Reporte por tienda (productos / con EAN / dias historial) ==")
    for t, v in (estado.get("reporte_tiendas") or {}).items():
        print(f"  {t:<16} productos={v['productos']:>5}  con_ean={v['con_ean']:>5}  dias={v['dias_historial']}")

    top = sorted(r, key=lambda x: -x["d"])[:10]
    print("\n== Top 10 por descuento ==")
    for i, x in enumerate(top, 1):
        print(f"{i}. {x['t']} | {x['n'][:55]} | Q{x['p']} (-{round(x['d']*100)}%)")
        print(f"   producto: {x['u']}")
        for m in (x.get("m") or []):
            print(f"   comparado: {m['t']} Q{m['p']}  {m['u']}")
        if x.get("et"):
            print(f"   etiqueta: {x['et']}")

    rng = random.Random(10)
    muestra = rng.sample(r, min(30, len(r)))
    print("\n== 30 al azar ==")
    for i, x in enumerate(muestra, 1):
        print(f"{i}. {x['t']} | {x['n'][:50]} | Q{x['p']} | {x['u']}")
        for m in (x.get("m") or [])[:1]:
            print(f"   vs {m['t']} Q{m['p']}  {m['u']}")


if __name__ == "__main__":
    main()
