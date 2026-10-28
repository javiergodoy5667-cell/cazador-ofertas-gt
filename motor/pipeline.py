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
from . import categorias, config, filtros, historial, mercado, puntaje

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

    # Excluir lo que no es oferta real (reservas, accesorios, kits, usados...).
    productos = [p for p in productos if not filtros.excluido(p.get("nombre", ""))]

    # Clasificar categoria unificada (se conserva la original de la tienda)
    for p in productos:
        p["categoria_tienda"] = p.get("categoria", "")
        p["categoria"] = categorias.clasificar(p.get("categoria_tienda", ""),
                                               p.get("nombre", ""))

    # Comparacion entre tiendas SOLO por EAN (auditoria 9).
    info_mercado = mercado.calcular(productos)

    # Registrar en historial por lotes (solo se anade linea si el precio cambia)
    por_tienda = {}
    for p in productos:
        por_tienda.setdefault(p["tienda"], []).append(p)
    for tienda, lista in por_tienda.items():
        try:
            historial.registrar_lote(tienda, lista)
        except Exception:
            continue

    # Podar historial viejo (>90 dias)
    max_dias = cfg.get("historial_max_dias", 90)
    for tienda in por_tienda:
        try:
            historial.podar(tienda, dias=max_dias)
        except Exception:
            continue

    # Indexar historial por id de producto
    idx = {}
    for tienda in por_tienda:
        for o in historial.cargar(tienda):
            idx.setdefault(o["id"], []).append(o)

    alertados = _cargar_alertados()
    ofertas = []
    for p in productos:
        try:
            o = puntaje.evaluar(p, idx.get(p["id"], []), alertados=alertados,
                                mercado=info_mercado.get(p["id"]))
        except Exception:
            o = None
        if o:
            ofertas.append(o)

    # Ordenar: activas por puntaje descendente; agotadas al final.
    activas = [o for o in ofertas if o["nivel"] != "agotado"]
    agotadas = [o for o in ofertas if o["nivel"] == "agotado"]
    activas.sort(key=lambda o: o["puntaje"], reverse=True)
    ofertas = activas + agotadas

    # Freno de seguridad: descuento >70% (precio <30% de la referencia) es error
    # de emparejamiento/datos. Se guarda para revision, NO se publica.
    sospechosos = []
    for p in productos:
        antes = p.get("precio_antes_tienda")
        if not antes or antes <= 0 or p.get("precio_actual", 0) <= 0:
            continue
        desc = (antes - p["precio_actual"]) / antes
        if desc > 0.70:
            sospechosos.append({
                "tienda": p["tienda"], "nombre": p.get("nombre", ""),
                "precio": p["precio_actual"], "antes": antes,
                "descuento": round(desc, 3), "url": p.get("url", ""),
            })
    (DATA / "sospechosos.json").write_text(
        json.dumps(sospechosos, ensure_ascii=False, indent=2), encoding="utf-8")

    (DATA / "ofertas.json").write_text(
        json.dumps(ofertas, ensure_ascii=False, indent=2), encoding="utf-8")

    # precios.json: id -> serie cronologica [{fecha, precio}] para la grafica.
    # Solo productos con >=2 observaciones (los de 1 no tienen grafica) para
    # que el archivo pese poco; la web lo carga de forma perezosa.
    precios = {}
    for pid, lista in idx.items():
        if len(lista) < 2:
            continue
        lista = sorted(lista, key=lambda o: o.get("fecha_inicio", ""))
        precios[pid] = [{"fecha": o.get("fecha_inicio"), "precio": o["precio"]}
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

    # Resumen LIGERO para las tarjetas (claves cortas) -> primera carga rapida.
    resumen = []
    for o in ofertas:
        resumen.append({
            "i": o["id"], "n": (o["nombre"] or "")[:80], "p": o["precio_actual"],
            "d": o["descuento_real"], "lv": o["nivel"], "t": o["tienda"],
            "c": o["categoria"], "img": o.get("imagen"), "u": o["url"],
            "m": [{"t": m["tienda"], "p": m["precio"], "u": m["url"]}
                  for m in o.get("mercado", [])],
            "f": o.get("fuente_referencia"), "ai": bool(o.get("antes_inflado")),
            "dr": o.get("precio_referencia"), "v": True,
            "et": o.get("etiqueta", ""),
            "mb": o.get("mas_barato_que"),
        })
    (WEB / "ofertas-resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")

    # Nota: el marcado de "alertados" (antispam) lo hace alertas/enviar.py
    # solo para lo que realmente se envio por Telegram.

    por_nivel = {}
    for o in ofertas:
        por_nivel[o["nivel"]] = por_nivel.get(o["nivel"], 0) + 1

    # Dias de historial acumulado (distintas fechas de inicio observadas).
    dias = {o.get("fecha_inicio") for lista in idx.values() for o in lista
            if o.get("fecha_inicio")}
    dias_historial = len(dias)

    con_ean = {}
    for p in productos:
        if p.get("ean"):
            con_ean[p["tienda"]] = con_ean.get(p["tienda"], 0) + 1

    # Reporte por tienda: productos, con EAN y dias de historial (span).
    reporte_tiendas = {}
    for tienda, lista in por_tienda.items():
        fechas = sorted({o["fecha_inicio"] for o in historial.cargar(tienda)
                         if o.get("fecha_inicio")})
        span = 0
        if fechas:
            try:
                span = (dt.date.fromisoformat(fechas[-1])
                        - dt.date.fromisoformat(fechas[0])).days + 1
            except ValueError:
                span = len(fechas)
        reporte_tiendas[tienda] = {
            "productos": len(lista),
            "con_ean": sum(1 for p in lista if p.get("ean")),
            "dias_historial": span,
        }

    inflado_ejemplos = []
    for p in productos:
        info = info_mercado.get(p["id"])
        if info and info["antes_inflado"] and len(inflado_ejemplos) < 5:
            inflado_ejemplos.append({
                "nombre": (p.get("nombre") or "")[:60],
                "tienda": p.get("tienda"),
                "antes": p.get("precio_antes_tienda"),
                "precio": p.get("precio_actual"),
                "max_otro": max(x["precio"] for x in info["mercado"]),
                "url": p.get("url"),
            })

    estado = {
        "ultima_corrida": dt.datetime.now(dt.timezone(dt.timedelta(hours=-6)))
                          .isoformat(timespec="seconds"),
        "duracion_seg": round(time.monotonic() - inicio, 1),
        "productos_leidos": len(productos),
        "dias_historial": dias_historial,
        "con_ean": con_ean,
        "reporte_tiendas": reporte_tiendas,
        "coincidencias": len(info_mercado),
        "antes_inflado": sum(1 for v in info_mercado.values() if v["antes_inflado"]),
        "inflado_ejemplos": inflado_ejemplos,
        "ofertas_por_nivel": por_nivel,
        "fuentes": fuentes,
        "fallos": [{"fuente": n, "error": e} for n, e in fallos],
    }
    (DATA / "estado.json").write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    (WEB / "estado.json").write_text(
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
