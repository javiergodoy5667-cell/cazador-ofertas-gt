# -*- coding: utf-8 -*-
"""
Alertas por Telegram (API HTTP, sin librerias externas).
- formatear_oferta(): arma el mensaje de cada oferta.
- enviar(): sendMessage / sendPhoto.
- obtener_chat_id(): lee getUpdates para descubrir el chat del usuario.
"""
import datetime as dt
import json
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/{metodo}"


def _post(token, metodo, datos):
    url = API.format(token=token, metodo=metodo)
    cuerpo = urllib.parse.urlencode(datos).encode("utf-8")
    req = urllib.request.Request(url, data=cuerpo, headers={
        "Content-Type": "application/x-www-form-urlencoded",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}


def horas_restantes(fin_oferta):
    """'2026-10-28T03:00:00Z' -> horas restantes (int) o None."""
    if not fin_oferta:
        return None
    try:
        d = dt.datetime.fromisoformat(fin_oferta.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        ahora = dt.datetime.now(dt.timezone.utc)
        horas = (d - ahora).total_seconds() / 3600
        return int(horas) if horas >= 0 else None
    except (ValueError, TypeError):
        return None


def formatear_oferta(o):
    """Arma el texto de una oferta con el formato del proyecto."""
    desc = round(o.get("descuento_real", 0) * 100)
    lineas = [
        f"{o.get('nivel_emoji','')} {o.get('nivel_label','')} · -{desc}% real",
        o.get("nombre", ""),
    ]
    precio = o.get("precio_actual", 0)
    ref = o.get("precio_referencia", 0)
    sufijo = " · mínimo histórico" if o.get("minimo_historico") else ""
    lineas.append(f"Q{precio:,.0f} (antes ~Q{ref:,.0f}{sufijo})")
    modo = "🛒 Pagar en línea" if o.get("modo_compra") == "en_linea" else "🏪 Ir a la tienda"
    lineas.append(f"🏬 {o.get('tienda','')} · {modo}")
    h = horas_restantes(o.get("fin_oferta"))
    if h is not None:
        lineas.append(f"⏰ Termina en {h} h")
    lineas.append(f"👉 {o.get('url','')}")
    return "\n".join(lineas)


def enviar(token, chat_id, texto):
    """Envia un mensaje de texto. Devuelve dict de respuesta de Telegram."""
    return _post(token, "sendMessage", {"chat_id": chat_id, "text": texto,
                                        "disable_web_page_preview": False})


def enviar_foto(token, chat_id, foto_url, caption):
    """Envia una foto con caption. Si falla la foto, cae a texto."""
    r = _post(token, "sendPhoto", {"chat_id": chat_id, "photo": foto_url,
                                   "caption": caption})
    if not r.get("ok"):
        r = enviar(token, chat_id, caption)
    return r


def obtener_chat_id(token):
    """Descubre el chat_id del usuario que le escribio 'hola' al bot."""
    url = API.format(token=token, metodo="getUpdates")
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return None, str(e)
    if not data.get("ok"):
        return None, data.get("description", "error desconocido")
    ids = []
    for u in data.get("result", []):
        msg = u.get("message") or u.get("channel_post")
        if msg and msg.get("chat"):
            ids.append(msg["chat"]["id"])
    if not ids:
        return None, "no hay mensajes todavia (escribe 'hola' al bot)"
    return ids[-1], None


def enviar_alertas(ofertas, token, chat_id, max_inmediatas=15):
    """Envia las alertas inmediatas (error/loca) y resume las demas.
    Devuelve (enviadas, resumen)."""
    inmediatas = [o for o in ofertas
                  if o["nivel"] in ("error", "loca") and o["alerta_nueva"]]
    inmediatas = inmediatas[:max_inmediatas]
    enviadas = 0
    for o in inmediatas:
        texto = formatear_oferta(o)
        r = enviar_foto(token, chat_id, o.get("imagen"), texto) if o.get("imagen") \
            else enviar(token, chat_id, texto)
        if r.get("ok"):
            enviadas += 1
    resto = len([o for o in ofertas
                 if o["nivel"] in ("error", "loca") and o["alerta_nueva"]]) - enviadas
    return enviadas, resto
