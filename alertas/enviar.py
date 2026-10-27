# -*- coding: utf-8 -*-
"""
Envia las alertas por Telegram leyendo data/ofertas.json.
- Inmediatas: nivel error (🚨) y loca (🔥) con alerta_nueva.
- Resumen agrupado: nivel muy_buena (⚡) cada 3 horas (horas GT multiples de 3).
Actualiza data/alertados.json solo para lo que realmente se envio (antispam).
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alertas import telegram as t

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
TZ = dt.timezone(dt.timedelta(hours=-6))


def _cargar(ruta, default):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def main():
    tok = os.environ.get("TELEGRAM_TOKEN")
    cid = os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not cid:
        print("Sin TELEGRAM_TOKEN/TELEGRAM_CHAT_ID: omito alertas.")
        return

    ofertas = _cargar(DATA / "ofertas.json", [])
    alertados = _cargar(DATA / "alertados.json", {})

    # --- Alertas inmediatas (error + loca) ---
    inmediatas = [o for o in ofertas
                  if o.get("nivel") in ("error", "loca") and o.get("alerta_nueva")]
    enviadas = 0
    for o in inmediatas[:15]:
        texto = t.formatear_oferta(o)
        r = (t.enviar_foto(tok, cid, o.get("imagen"), texto)
             if o.get("imagen") else t.enviar(tok, cid, texto))
        if r.get("ok"):
            enviadas += 1
            alertados[o["id"]] = o["precio_actual"]
    if len(inmediatas) > 15:
        t.enviar(tok, cid, f"+{len(inmediatas) - 15} ofertas más en la página\n"
                           + os.environ.get("PAGES_URL", ""))

    # --- Resumen agrupado de muy buenas cada 3 h ---
    hora = dt.datetime.now(TZ).hour
    if hora % 3 == 0:
        mbs = [o for o in ofertas
               if o.get("nivel") == "muy_buena" and o.get("alerta_nueva")]
        if mbs:
            top = sorted(mbs, key=lambda o: o["puntaje"], reverse=True)[:10]
            lineas = [f"⚡ Resumen de ofertas muy buenas ({len(mbs)} vigentes):"]
            for o in top:
                lineas.append(
                    f"• −{round(o['descuento_real'] * 100)}% {o['nombre'][:48]} "
                    f"— Q{o['precio_actual']:,.0f} · {o['tienda']}")
            lineas.append("👉 " + os.environ.get("PAGES_URL", ""))
            if t.enviar(tok, cid, "\n".join(lineas)).get("ok"):
                for o in mbs:
                    alertados[o["id"]] = o["precio_actual"]

    (DATA / "alertados.json").write_text(
        json.dumps(alertados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Alertas inmediatas enviadas: {enviadas}")


if __name__ == "__main__":
    main()
