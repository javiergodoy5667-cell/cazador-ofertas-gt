# -*- coding: utf-8 -*-
"""
Cargador minimo de config.yml (sin dependencias externas).
Soporta: claves planas `key: valor`, listas inline `[a, b]` y anidacion
de un nivel (`niveles:` seguido de `  loca: 0.5`).
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RUTA = BASE / "config" / "config.yml"


def _valor(s):
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [x.strip().strip("'\"") for x in inner.split(",")] if inner else []
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if s in ("null", "None", ""):
        return None
    try:
        return float(s) if "." in s else int(s)
    except ValueError:
        return s.strip("'\"")


def cargar(ruta=None):
    ruta = Path(ruta) if ruta else RUTA
    data = {}
    seccion = None
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        sin_com = linea.split("#", 1)[0]
        if not sin_com.strip():
            continue
        indent = len(sin_com) - len(sin_com.lstrip(" "))
        contenido = sin_com.strip()
        if contenido.startswith("- "):
            if seccion is not None:
                if not isinstance(data.get(seccion), list):
                    data[seccion] = []   # convertir el placeholder dict en lista
                data[seccion].append(_valor(contenido[2:]))
            continue
        if ":" not in contenido:
            continue
        k, v = contenido.split(":", 1)
        k = k.strip()
        v = v.strip()
        if indent == 0:
            seccion = k
            data[k] = _valor(v) if v else {}
        else:
            if seccion and isinstance(data.get(seccion), dict):
                data[seccion][k] = _valor(v)
    return data
