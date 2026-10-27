# -*- coding: utf-8 -*-
"""
Historial de precios en JSONL. Una linea SOLO cuando el precio CAMBIA
(no cada dia), con `fecha_inicio` y `visto_hasta` para saber cuanto estuvo
vigente. Asi el archivo crece poco (auditoria: antes ~3.7 MB/dia).
"""
import datetime as dt
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
HISTORIAL_DIR = BASE / "data" / "historial"

TZ = dt.timezone(dt.timedelta(hours=-6))  # America/Guatemala
TOLERANCIA = 0.005  # para comparar precios float


def hoy_gt():
    return dt.datetime.now(TZ).date()


def ruta(tienda):
    return HISTORIAL_DIR / f"{tienda}.jsonl"


def cargar(tienda):
    """Devuelve lista de observaciones ({id, fecha_inicio, precio, visto_hasta})."""
    p = ruta(tienda)
    if not p.exists():
        return []
    out = []
    for linea in p.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            out.append(json.loads(linea))
        except json.JSONDecodeError:
            continue
    return out


def _escribir(p, obs):
    p.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in obs),
                 encoding="utf-8")


def registrar_lote(tienda, productos, fecha=None):
    """Registra un lote de productos. Solo se anade linea si el precio cambia.
    Devuelve cuantas lineas nuevas se escribieron."""
    fecha = fecha or hoy_gt()
    fecha_s = fecha.isoformat()
    ayer = (fecha - dt.timedelta(days=1)).isoformat()
    HISTORIAL_DIR.mkdir(parents=True, exist_ok=True)
    obs = cargar(tienda)
    ultimo = {}
    for i, o in enumerate(obs):
        ultimo[o["id"]] = i
    nuevos = 0
    for prod in productos:
        pid = prod["id"]
        precio = prod["precio_actual"]
        i = ultimo.get(pid)
        if i is not None and abs(obs[i].get("precio", -1) - precio) < TOLERANCIA:
            obs[i]["visto_hasta"] = fecha_s  # mismo precio: solo extender vigencia
        else:
            if i is not None:
                obs[i]["visto_hasta"] = ayer  # cerrar la linea anterior
            obs.append({
                "id": pid,
                "fecha_inicio": fecha_s,
                "precio": precio,
                "visto_hasta": fecha_s,
                "precio_unidad": prod.get("precio_unidad"),
                "unidad": prod.get("unidad"),
            })
            ultimo[pid] = len(obs) - 1
            nuevos += 1
    _escribir(ruta(tienda), obs)
    return nuevos


def registrar(tienda, producto, fecha=None):
    """Conveniencia para pruebas: registra un solo producto."""
    return registrar_lote(tienda, [producto], fecha)


def podar(tienda, dias=90, fecha=None):
    """Borra lineas cuya vigencia (visto_hasta) termino hace mas de `dias`."""
    fecha = fecha or hoy_gt()
    limite = fecha - dt.timedelta(days=dias)
    obs = cargar(tienda)
    quedan, quitados = [], 0
    for o in obs:
        try:
            vh = dt.date.fromisoformat(o.get("visto_hasta")
                                       or o.get("fecha_inicio")
                                       or o.get("fecha"))
        except (KeyError, ValueError):
            quitados += 1
            continue
        if vh < limite:
            quitados += 1
        else:
            quedan.append(o)
    _escribir(ruta(tienda), quedan)
    return quitados
