# -*- coding: utf-8 -*-
"""
Pipeline: recolecta -> registra historial -> evalua -> escribe salidas.
Salidas en data/:
  - ofertas.json   (ofertas vigentes ordenadas por puntaje)
  - estado.json    (fuentes OK/rotas, productos leidos, duracion)
  - alertados.json (ultimo precio alertado por producto, para antispam)
"""
import concurrent.futures as cf
import datetime as dt
import json
import sys
import time
from pathlib import Path

from recolectores import RECOLECTORES
from . import config, historial, puntaje

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)


def _cargar_alertados():
    p = DATA / "alertados.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _guardar_alertados(d):
    (DATA / "alertados.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _recolectar_todo():
    resultados = {}
    fallos = []
    with cf.ThreadPoolExecutor(max_workers=len(RECOLECTORES)) as ex:
        futs = {ex.submit(m.recolectar): m.__name__ for m in RECOLECTORES}
        for f in cf.as_completed(futs):
            nombre = futs[f]
            try:
                resultados[nombre] = f.result()
            except Exception as e:
                resultados[nombre] = []
                fallos.append((nombre, f"{type(e).__name__}: {e}"))
    return resultados, fallos


def ejecutar(productos=None):
    """Ejecuta el pipeline. Si `productos` se pasa, no recolecta de red."""
    inicio = time.monotonic()
    cfg = config.cargar()

    fuentes = {}
    fallos = []
    if productos is None:
        resultados, fallos = _recolectar_todo()
        productos = []
        for nombre, lista in resultados.items():
            fuentes[nombre] = {"productos": len(lista),
                               "estado": "OK" if lista else "ROTA"}
            productos.extend(lista)
    else:
        for p in productos:
            fuentes.setdefault(p["tienda"], {"productos": 0, "estado": "OK"})
            fuentes[p["tienda"]]["productos"] += 1

    # Registrar en historial (una observacion por producto/dia)
    for p in productos:
        try:
            historial.registrar(p["tienda"], p)
        except Exception:
            continue

    # Podar historial viejo (>90 dias)
    max_dias = cfg.get("historial_max_dias", 90)
    for tienda in {p["tienda"] for p in productos}:
        try:
            historial.podar(tienda, dias=max_dias)
        except Exception:
            continue

    # Indexar historial por id de producto
    idx = {}
    for tienda in {p["tienda"] for p in productos}:
        for o in historial.cargar(tienda):
            idx.setdefault(o["id"], []).append(o)

    alertados = _cargar_alertados()
    ofertas = []
    for p in productos:
        try:
            o = puntaje.evaluar(p, idx.get(p["id"], []), alertados=alertados)
        except Exception:
            o = None
        if o:
            ofertas.append(o)

    # Ordenar: activas por puntaje descendente; agotadas al final.
    activas = [o for o in ofertas if o["nivel"] != "agotado"]
    agotadas = [o for o in ofertas if o["nivel"] == "agotado"]
    activas.sort(key=lambda o: o["puntaje"], reverse=True)
    ofertas = activas + agotadas

    (DATA / "ofertas.json").write_text(
        json.dumps(ofertas, ensure_ascii=False, indent=2), encoding="utf-8")

    # precios.json: id -> serie cronologica [{fecha, precio}] para la grafica.
    precios = {}
    for pid, lista in idx.items():
        lista = sorted(lista, key=lambda o: o.get("fecha", ""))
        precios[pid] = [{"fecha": o["fecha"], "precio": o["precio"]}
                        for o in lista]
    (DATA / "precios.json").write_text(
        json.dumps(precios, ensure_ascii=False, indent=2), encoding="utf-8")

    # Copias para la web (GitHub Pages sirve desde web/).
    WEB = BASE / "web"
    WEB.mkdir(exist_ok=True)
    (WEB / "ofertas.json").write_text(
        json.dumps(ofertas, ensure_ascii=False, indent=2), encoding="utf-8")
    (WEB / "precios.json").write_text(
        json.dumps(precios, ensure_ascii=False, indent=2), encoding="utf-8")

    # Nota: el marcado de "alertados" (antispam) lo hace alertas/enviar.py
    # solo para lo que realmente se envio por Telegram.

    por_nivel = {}
    for o in ofertas:
        por_nivel[o["nivel"]] = por_nivel.get(o["nivel"], 0) + 1

    estado = {
        "ultima_corrida": dt.datetime.now(dt.timezone(dt.timedelta(hours=-6)))
                          .isoformat(timespec="seconds"),
        "duracion_seg": round(time.monotonic() - inicio, 1),
        "productos_leidos": len(productos),
        "ofertas_por_nivel": por_nivel,
        "fuentes": fuentes,
        "fallos": [{"fuente": n, "error": e} for n, e in fallos],
    }
    (DATA / "estado.json").write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")

    return ofertas


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    res = ejecutar()
    print(f"Ofertas detectadas: {len(res)}")
    for o in res[:10]:
        if o["nivel"] != "agotado":
            print(f"  {o['nivel_emoji']} {o['nivel_label']:<24} "
                  f"-{o['descuento_real']*100:4.0f}%  {o['tienda']:<12} "
                  f"Q{o['precio_actual']:>9}  {o['nombre'][:40]}")
