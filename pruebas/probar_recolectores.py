# -*- coding: utf-8 -*-
"""
Prueba de la Fase 1: corre todos los recolectores en paralelo, imprime
cuantos productos trajo cada uno y FALLA (exit 1) si alguno trae 0.
Uso:  python -m pruebas.probar_recolectores
"""
import concurrent.futures as cf
import datetime as dt
import json
import sys
from pathlib import Path

from recolectores import RECOLECTORES

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    resultados = {}
    with cf.ThreadPoolExecutor(max_workers=len(RECOLECTORES)) as ex:
        futs = {ex.submit(m.recolectar): m.__name__ for m in RECOLECTORES}
        for f in cf.as_completed(futs):
            name = futs[f]
            try:
                resultados[name] = f.result()
            except Exception as e:
                resultados[name] = []
                print(f"ERROR {name}: {type(e).__name__}: {e}")

    fallos = []
    print("\n=== Recoleccion por fuente ===")
    for m in RECOLECTORES:
        name = m.__name__
        n = len(resultados.get(name, []))
        print(f"  {name:<10} {n:>4} productos")
        if n == 0:
            fallos.append(name)

    # Guardar evidencia (una coleccion combinada con timestamp)
    todo = []
    for m in RECOLECTORES:
        for p in resultados.get(m.__name__, []):
            todo.append(p)
    evidencia = DATA / f"recoleccion_{dt.datetime.now():%Y%m%d-%H%M%S}.json"
    evidencia.write_text(json.dumps(todo, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    print(f"\nTotal: {len(todo)} productos | evidencia: {evidencia}")

    if fallos:
        print(f"\nFALLO: estas fuentes trajeron 0 productos: {', '.join(fallos)}")
        sys.exit(1)
    print("OK: todas las fuentes trajeron productos.")


if __name__ == "__main__":
    main()
