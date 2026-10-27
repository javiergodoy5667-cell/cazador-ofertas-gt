# -*- coding: utf-8 -*-
"""
Prueba de Telegram. Lee el token y el chat_id de variables de entorno
(no se guardan secretos en el codigo). Uso:
  $env:TELEGRAM_TOKEN = "..."   (PowerShell)
  python scripts/probar_telegram.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alertas import telegram as t


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tok = os.environ.get("TELEGRAM_TOKEN")
    if not tok:
        print("Falta la variable de entorno TELEGRAM_TOKEN")
        return
    cid = os.environ.get("TELEGRAM_CHAT_ID")
    if not cid:
        cid, err = t.obtener_chat_id(tok)
        if err:
            print(f"No pude detectar el chat_id: {err}")
            print("Abre tu bot en Telegram y escribele 'hola', luego vuelve a correr.")
            return
        print(f"chat_id detectado: {cid}")
    r = t.enviar(tok, cid, "✅ Prueba de Cazador GT: las alertas funcionan.")
    print("sendMessage ->", "OK" if r.get("ok") else f"FALLO {r.get('description')}")


if __name__ == "__main__":
    main()
