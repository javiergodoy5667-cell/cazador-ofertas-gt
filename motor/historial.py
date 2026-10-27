# -*- coding: utf-8 -*-
"""
Historial de precios en archivos JSONL (una linea por observacion).
data/historial/<tienda>.jsonl
Reglas:
  - maximo 1 observacion por producto por dia.
  - se borran observaciones con mas de 90 dias.
"""
import datetime as dt
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
HISTORIAL_DIR = BASE / "data" / "historial"

TZ = dt.timezone(dt.timedelta(hours=-6))  # America/Guatemala


def hoy_gt():
    return dt.datetime.now(TZ).date()


def ruta(tienda):
    return HISTORIAL_DIR / f"{tienda}.jsonl"


def cargar(tienda):
    """Devuelve lista de observaciones ({id, fecha, precio, ...})."""
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


def registrar(tienda, producto, fecha=None):
    """Añade una observacion si no existe ya una para (id, fecha) hoy.
    Devuelve True si se escribio algo nuevo."""
    fecha = (fecha or hoy_gt()).isoformat()
    HISTORIAL_DIR.mkdir(parents=True, exist_ok=True)
    p = ruta(tienda)
    obs = cargar(tienda)
    for o in obs:
        if o.get("id") == producto["id"] and o.get("fecha") == fecha:
            return False
    linea = {
        "id": producto["id"],
        "fecha": fecha,
        "precio": producto["precio_actual"],
        "precio_unidad": producto.get("precio_unidad"),
        "unidad": producto.get("unidad"),
        "visto_en": producto.get("visto_en"),
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    return True


def podar(tienda, dias=90, fecha=None):
    """Borra observaciones mas viejas que `dias`. Devuelve cuantas quito."""
    fecha = fecha or hoy_gt()
    limite = fecha - dt.timedelta(days=dias)
    obs = cargar(tienda)
    quedan = []
    quitados = 0
    for o in obs:
        try:
            d = dt.date.fromisoformat(o["fecha"])
        except (KeyError, ValueError):
            quitados += 1
            continue
        if d < limite:
            quitados += 1
        else:
            quedan.append(o)
    p = ruta(tienda)
    if p.exists():
        p.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n"
                             for o in quedan), encoding="utf-8")
    return quitados
