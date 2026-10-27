# -*- coding: utf-8 -*-
"""
Base compartida de los recolectores.
- get(): HTTP con SSL opcional, reintentos con espera creciente y límite
  de 1 pedido por segundo por dominio (cortesía, robots.txt).
- limpiar_precio(): "Q1,299.00" -> 1299.0
- ahora_gt(): timestamp ISO en America/Guatemala.
Solo biblioteca estándar.
"""

import datetime as dt
import gzip
import re
import ssl
import threading
import time
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
TIMEOUT = 20
REINTENTOS = 3
ESPERAS = [5, 20, 60]  # segundos entre reintentos

# dominio -> instante del ultimo pedido (para no superar 1 req/s)
_throttle = {}
_throttle_lock = threading.Lock()


def _esperar_cortesia(host):
    with _throttle_lock:
        ahora = time.monotonic()
        ultimo = _throttle.get(host, 0)
        espera = 1.0 - (ahora - ultimo)
        if espera > 0:
            time.sleep(espera)
        _throttle[host] = time.monotonic()


def get(url, timeout=TIMEOUT, reintentos=REINTENTOS, host=None):
    """GET devolviendo (status, final_url, texto). 3 reintentos con backoff."""
    from urllib.parse import urlparse
    host = host or urlparse(url).netloc
    for intento in range(reintentos):
        _esperar_cortesia(host)
        for verify in (True, False):
            ctx = (ssl.create_default_context() if verify
                   else ssl._create_unverified_context())
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "application/json,text/html,application/xml,*/*;q=0.9",
                "Accept-Encoding": "gzip",
                "Accept-Language": "es-GT,es;q=0.9,en;q=0.8",
            })
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                    raw = r.read()
                    if r.headers.get("Content-Encoding", "").lower() == "gzip":
                        raw = gzip.decompress(raw)
                    return r.status, r.geturl(), raw.decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                return e.code, url, ""
            except Exception as e:
                if "CERTIFICATE" in str(e).upper():
                    continue  # reintentar sin verificar
                # error de red: reintentar mas tarde
                break
        if intento < reintentos - 1:
            time.sleep(ESPERAS[min(intento, len(ESPERAS) - 1)])
    return None, url, ""


def limpiar_precio(v):
    """'Q1,299.00' / '1299.00' / 1299 -> float. None si invalido."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("Q", "").replace(",", "").replace(" ", "").strip()
    m = re.search(r"-?\d+(\.\d+)?", s)
    if not m:
        return None
    return round(float(m.group()), 2)


def ahora_gt():
    """Timestamp ISO 8601 en America/Guatemala (UTC-6, sin horario de verano)."""
    utc = dt.timezone(dt.timedelta(hours=-6))
    return dt.datetime.now(utc).isoformat(timespec="seconds")


def normalizar_ean(v):
    """Deja solo digitos del codigo de barras. '' si no valido (>=8 digitos)."""
    import re
    if v is None:
        return ""
    d = re.sub(r"\D", "", str(v))
    return d if len(d) >= 8 else ""


def nuevo_producto(id_, tienda, nombre, precio, antes, url, imagen,
                   categoria="", disponible=True, modo_compra="en_linea",
                   fin_oferta=None, ean="", marca="", modelo=""):
    """Construye el dict estandar de producto."""
    return {
        "id": id_,
        "tienda": tienda,
        "nombre": nombre,
        "categoria": categoria,
        "precio_actual": precio,
        "precio_antes_tienda": antes,
        "moneda": "GTQ",
        "url": url,
        "imagen": imagen,
        "disponible": bool(disponible),
        "modo_compra": modo_compra,
        "fin_oferta": fin_oferta,
        "ean": normalizar_ean(ean),
        "marca": (marca or "").strip(),
        "modelo": (modelo or "").strip(),
        "visto_en": ahora_gt(),
    }
