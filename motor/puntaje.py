# -*- coding: utf-8 -*-
"""
Motor de puntaje. Mide el descuento real contra el historial propio
(no contra el "precio antes" que la tienda puede inflar).

Entrada: un producto (dict) y las observaciones de su historial.
Salida: dict de oferta con nivel y puntaje, o None si se ignora.
"""
import datetime as dt
import statistics

NIVELES = {
    "error":     {"emoji": "🚨", "label": "POSIBLE ERROR DE PRECIO", "orden": 0},
    "loca":      {"emoji": "🔥", "label": "LOCA", "orden": 1},
    "muy_buena": {"emoji": "⚡", "label": "MUY BUENA", "orden": 2},
    "buena":     {"emoji": "✅", "label": "BUENA", "orden": 3},
    "agotado":   {"emoji": "·", "label": "agotado", "orden": 9},
}

VENTANA_DIAS = 30
MIN_OBS_DIAS = 3
PRECIO_BASURA = 15.0


def _subir(nivel):
    """Sube un nivel de urgencia (buena -> muy_buena -> loca -> error)."""
    orden = NIVELES[nivel]["orden"]
    nuevo = max(0, orden - 1)
    for k, v in NIVELES.items():
        if v["orden"] == nuevo:
            return k
    return nivel


def _relampago(prod, ahora=None):
    """Una oferta es relampago si la tienda muestra fin proximo o etiqueta."""
    nombre = (prod.get("nombre") or "").lower()
    if any(t in nombre for t in ("flash", "relampago", "relámpago", "hoy")):
        return True
    fin = prod.get("fin_oferta")
    if not fin:
        return False
    try:
        d = dt.datetime.fromisoformat(fin.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        ahora = ahora or dt.datetime.now(dt.timezone.utc)
        return (d - ahora) <= dt.timedelta(hours=48)
    except (ValueError, TypeError):
        return False


def precio_referencia(obs, hoy, prod=None):
    """Devuelve (referencia, sin_historial, usa_unidad).
    referencia = mediana de precios (o precio por unidad) de los ultimos
    30 dias, exigiendo >=3 observaciones en dias distintos.
    Si no alcanza, devuelve (None, True, ...).
    """
    ventana = hoy - dt.timedelta(days=VENTANA_DIAS)
    relevantes = []
    for o in obs:
        try:
            d = dt.date.fromisoformat(o["fecha"])
        except (KeyError, ValueError):
            continue
        if d >= ventana:
            relevantes.append(o)
    # comparacion por unidad (evita falsos descuentos por cambio de tamano)
    if prod and prod.get("precio_unidad") is not None and prod.get("unidad"):
        vals = [o for o in relevantes
                if o.get("unidad") == prod["unidad"]
                and o.get("precio_unidad") is not None]
        if len({o["fecha"] for o in vals}) >= MIN_OBS_DIAS:
            return (statistics.median([o["precio_unidad"] for o in vals]),
                    False, True)
        return None, True, True
    if len({o["fecha"] for o in relevantes}) >= MIN_OBS_DIAS:
        return statistics.median([o["precio"] for o in relevantes]), False, False
    return None, True, False


def evaluar(prod, obs, hoy=None, alertados=None):
    """Evalua un producto contra su historial. Devuelve oferta o None."""
    hoy = hoy or dt.date.today()
    actual = prod.get("precio_actual")
    if actual is None or actual <= 0:
        return None
    disponible = bool(prod.get("disponible", True))

    ref, sin_hist, usa_unidad = precio_referencia(obs, hoy, prod)

    # Precio que se compara (por unidad si aplica, si no el total).
    if usa_unidad:
        comparar = prod.get("precio_unidad")
        if comparar is None or comparar <= 0:
            return None
    else:
        comparar = actual

    if sin_hist:
        antes = prod.get("precio_antes_tienda")
        if antes is None or antes <= 0:
            ref = comparar
        else:
            ref = antes
    if ref <= 0:
        ref = comparar

    descuento = (ref - comparar) / ref if ref > 0 else 0.0

    # Minimo historico: se compara contra dias ANTERIORES (no contra hoy,
    # para no marcar "minimo" el primer dia que aparece el producto).
    hoy_iso = hoy.isoformat()
    if usa_unidad:
        previos = [o["precio_unidad"] for o in obs
                   if o.get("fecha") != hoy_iso and o.get("precio_unidad") is not None]
        minimo = bool(previos) and comparar <= min(previos)
    else:
        previos = [o["precio"] for o in obs if o.get("fecha") != hoy_iso]
        minimo = bool(previos) and comparar <= min(previos)

    relampago = _relampago(prod)
    ahorro = max(0.0, ref - comparar)

    # Productos basura: ignorar precio final < Q15, salvo error de precio.
    if actual < PRECIO_BASURA and not (descuento > 0.65 and not sin_hist):
        return None

    # Nivel base
    if descuento > 0.65 and not sin_hist:
        nivel = "error"
    elif descuento >= 0.50:
        nivel = "loca"
    elif descuento >= 0.35 or (minimo and descuento >= 0.20):
        nivel = "muy_buena"
    elif descuento >= 0.20:
        nivel = "buena"
    else:
        return None

    # Sin historial: nunca se avisa por Telegram; maximo nivel "buena" (web).
    if sin_hist and nivel in ("error", "loca", "muy_buena"):
        nivel = "buena"
    if relampago:
        nivel = _subir(nivel)
    if not disponible:
        nivel = "agotado"

    puntaje = (descuento * 100
               + min(ahorro / 50.0, 30.0)
               + (15 if relampago else 0)
               + (10 if minimo else 0)
               - (20 if sin_hist else 0))

    oferta = {
        "id": prod.get("id"),
        "tienda": prod.get("tienda"),
        "nombre": prod.get("nombre"),
        "categoria": prod.get("categoria", ""),
        "url": prod.get("url"),
        "imagen": prod.get("imagen"),
        "moneda": prod.get("moneda", "GTQ"),
        "precio_actual": actual,
        "precio_referencia": round(ref, 2),
        "precio_antes_tienda": prod.get("precio_antes_tienda"),
        "descuento_real": round(descuento, 4),
        "ahorro_q": round(ahorro, 2),
        "minimo_historico": minimo,
        "sin_historial": sin_hist,
        "relampago": relampago,
        "nivel": nivel,
        "nivel_emoji": NIVELES[nivel]["emoji"],
        "nivel_label": NIVELES[nivel]["label"],
        "puntaje": round(puntaje, 1),
        "disponible": disponible,
        "modo_compra": prod.get("modo_compra", "en_linea"),
        "fin_oferta": prod.get("fin_oferta"),
        "visto_en": prod.get("visto_en"),
    }

    oferta["alerta_nueva"] = debe_alertar(prod["id"], actual, alertados or {})
    return oferta


def debe_alertar(pid, precio, alertados):
    """True si el producto debe alertarse: nunca alertado, o precio cayo >=5%."""
    ultimo = alertados.get(pid)
    if ultimo is None:
        return True
    if ultimo <= 0:
        return True
    return (ultimo - precio) / ultimo >= 0.05
