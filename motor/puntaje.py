# -*- coding: utf-8 -*-
"""
Motor de puntaje. La referencia (en orden de confianza) es:
  1) historial propio >= 3 dias (mediana)
  2) precio de mercado en otras tiendas (comparacion por EAN / marca+modelo)
  3) nada -> el producto NO es oferta.
El "precio antes" de la tienda NUNCA se usa para calcular niveles.
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

VENTANA_DIAS = 7
MIN_OBS_DIAS = 3
PRECIO_BASURA = 15.0


def _subir(nivel):
    orden = NIVELES[nivel]["orden"]
    nuevo = max(0, orden - 1)
    for k, v in NIVELES.items():
        if v["orden"] == nuevo:
            return k
    return nivel


def _relampago(prod):
    """Relampago SOLO con etiqueta explicita (fin_oferta de VTEX es un default)."""
    nombre = (prod.get("nombre") or "").lower()
    marcas = ("flash", "relampago", "relámpago", "oferta del dia",
              "oferta del día", "solo hoy", "oferta de hoy", "deal del dia",
              "deal del día", "hot sale", "liquidacion relampago")
    return any(m in nombre for m in marcas)


def _dias_activos(o, hoy, ventana=VENTANA_DIAS):
    try:
        inicio = dt.date.fromisoformat(o.get("fecha_inicio") or o.get("fecha"))
        fin = dt.date.fromisoformat(o.get("visto_hasta")
                                    or o.get("fecha_inicio") or o.get("fecha"))
    except (KeyError, ValueError, TypeError):
        return []
    a = max(inicio, hoy - dt.timedelta(days=ventana))
    b = min(fin, hoy)
    if a > b:
        return []
    return [(a + dt.timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


def precio_referencia(obs, hoy, prod=None):
    """Mediana de los ultimos 30 dias expandiendo dias activos.
    Devuelve (referencia, sin_historial, usa_unidad)."""
    expandido = []
    for o in obs:
        for d in _dias_activos(o, hoy):
            expandido.append((d, o))
    if prod and prod.get("precio_unidad") is not None and prod.get("unidad"):
        pares = [(d, o) for d, o in expandido
                 if o.get("unidad") == prod["unidad"]
                 and o.get("precio_unidad") is not None]
        if len({d for d, _ in pares}) >= MIN_OBS_DIAS:
            return (statistics.median([o["precio_unidad"] for _, o in pares]),
                    False, True)
        return None, True, True
    if len({d for d, _ in expandido}) >= MIN_OBS_DIAS:
        return statistics.median([o["precio"] for _, o in expandido]), False, False
    return None, True, False


def evaluar(prod, obs, hoy=None, alertados=None, mercado=None):
    """Evalua un producto. Devuelve oferta o None (sin referencia = no oferta)."""
    hoy = hoy or dt.date.today()
    actual = prod.get("precio_actual")
    if actual is None or actual <= 0:
        return None
    disponible = bool(prod.get("disponible", True))

    ref_hist, sin_hist, usa_unidad = precio_referencia(obs, hoy, prod)
    if usa_unidad:
        comparar = prod.get("precio_unidad")
        if comparar is None or comparar <= 0:
            return None
    else:
        comparar = actual

    # Referencia: historial > mercado > nada.
    if not sin_hist:
        ref, fuente = ref_hist, "historial"
    elif mercado and mercado.get("precio_mercado"):
        ref, fuente = mercado["precio_mercado"], "mercado"
    else:
        return None
    if ref <= 0:
        return None

    # "antes" inflado: se descarta (no se promociona).
    if mercado and mercado.get("antes_inflado"):
        return None

    descuento = (ref - comparar) / ref

    # Minimo historico (solo con historial real).
    hoy_iso = hoy.isoformat()
    if usa_unidad:
        previos = [o["precio_unidad"] for o in obs
                   if (o.get("fecha_inicio") or o.get("fecha", "")) < hoy_iso
                   and o.get("precio_unidad") is not None]
        minimo = fuente == "historial" and bool(previos) and comparar <= min(previos)
    else:
        previos = [o["precio"] for o in obs
                   if (o.get("fecha_inicio") or o.get("fecha", "")) < hoy_iso]
        minimo = fuente == "historial" and bool(previos) and comparar <= min(previos)

    relampago = _relampago(prod)
    ahorro = max(0.0, ref - comparar)

    # Freno de seguridad (auditoria 9): si el precio es <30% de la referencia
    # es error de emparejamiento/datos -> NO es oferta (se guarda aparte).
    if descuento > 0.70:
        return None

    if actual < PRECIO_BASURA and descuento < 0.55:
        return None

    if fuente == "historial":
        if descuento > 0.65:
            nivel = "error"
        elif descuento >= 0.50:
            nivel = "loca"
        elif descuento >= 0.35 or (minimo and descuento >= 0.20):
            nivel = "muy_buena"
        elif descuento >= 0.20:
            nivel = "buena"
        else:
            return None
    else:  # mercado sin historial propio
        # Auditoria 10: ser mas barato que otra tienda NO es oferta fuerte.
        # Maximo nivel "buena" y con etiqueta "Mas barato que <tienda>".
        if descuento >= 0.15:
            nivel = "buena"
        else:
            return None

    if relampago:
        nivel = _subir(nivel)
    if not disponible:
        nivel = "agotado"

    puntaje = (descuento * 100
               + min(ahorro / 50.0, 30.0)
               + (15 if relampago else 0)
               + (10 if minimo else 0))

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
        "fuente_referencia": fuente,
        "mercado": (mercado or {}).get("mercado", []),
        "antes_inflado": bool((mercado or {}).get("antes_inflado")),
        "mas_barato_que": (mercado or {}).get("mas_barato_que"),
        "etiqueta": (f"Más barato que {(mercado or {}).get('mas_barato_que', {}).get('tienda')}"
                     if fuente == "mercado" and (mercado or {}).get("mas_barato_que")
                     else ""),
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
    ultimo = alertados.get(pid)
    if ultimo is None:
        return True
    if ultimo <= 0:
        return True
    return (ultimo - precio) / ultimo >= 0.05
