# -*- coding: utf-8 -*-
"""
Envia las alertas por Telegram.
- Inmediatas: 🚨 error SIEMPRE (cualquier categoria) + 🔥 loca solo si su
  categoria esta en config.categorias_alerta. Cada aviso empieza con el emoji
  de su categoria.
- Resumen diario a las 7:00 (hora GT): top 3 de cada categoria de alerta.
Actualiza data/alertados.json solo para lo que realmente se envio.
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alertas import telegram as t
from motor import config

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

    cfg = config.cargar()
    alerta_cats = set(cfg.get("categorias_alerta", []))
    ofertas = _cargar(DATA / "ofertas.json", [])
    alertados = _cargar(DATA / "alertados.json", {})
    pages = os.environ.get("PAGES_URL", "")

    # --- Inmediatas (nunca las marcadas "revisar") ---
    inmediatas = [o for o in ofertas if o.get("alerta_nueva")
                  and not o.get("revisar") and (
        o.get("nivel") == "error" or
        (o.get("nivel") == "loca" and o.get("categoria") in alerta_cats))]
    enviadas = 0
    for o in inmediatas[:15]:
        texto = t.formatear_oferta(o)
        r = (t.enviar_foto(tok, cid, o.get("imagen"), texto)
             if o.get("imagen") else t.enviar(tok, cid, texto))
        if r.get("ok"):
            enviadas += 1
            alertados[o["id"]] = o["precio_actual"]
    if len(inmediatas) > 15:
        t.enviar(tok, cid, f"+{len(inmediatas) - 15} ofertas más en la página\n{pages}")

    # --- Resumen diario 7:00 GT, agrupado por categoria (top 3) ---
    if dt.datetime.now(TZ).hour == 7:
        por_cat = {}
        for o in ofertas:
            if o.get("nivel") == "agotado" or o.get("categoria") not in alerta_cats:
                continue
            por_cat.setdefault(o["categoria"], []).append(o)
        if por_cat:
            lineas = ["📅 Resumen de hoy por categoría:"]
            orden = sorted(por_cat,
                           key=lambda c: -max((x["puntaje"] for x in por_cat[c]),
                                              default=0))
            for cat in orden:
                top = sorted(por_cat[cat], key=lambda x: x["puntaje"], reverse=True)[:3]
                lineas.append(f"\n{cat}")
                for o in top:
                    lineas.append(f"  • −{round(o['descuento_real'] * 100)}% "
                                  f"{o['nombre'][:40]} — Q{o['precio_actual']:,.0f}")
            lineas.append(f"\n👉 {pages}")
            t.enviar(tok, cid, "\n".join(lineas))

    (DATA / "alertados.json").write_text(
        json.dumps(alertados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Alertas inmediatas enviadas: {enviadas}")


if __name__ == "__main__":
    main()
