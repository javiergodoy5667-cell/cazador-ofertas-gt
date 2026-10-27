# -*- coding: utf-8 -*-
"""Verifica que los enlaces de producto de las muestras respondan 200."""
import json, ssl, urllib.request, gzip, sys
from pathlib import Path

MUESTRAS = Path(__file__).resolve().parent.parent / "muestras"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def status(url):
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return f"ERR {type(e).__name__}"

for f in sorted(MUESTRAS.glob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    if not data:
        continue
    ok = 0
    for p in data[:5]:
        u = p.get("url")
        st = status(u) if u else "sin url"
        if st == 200:
            ok += 1
        print(f"{f.stem:<12} {st!s:<8} {u}")
    print(f"  -> {ok}/5 enlaces OK\n")
