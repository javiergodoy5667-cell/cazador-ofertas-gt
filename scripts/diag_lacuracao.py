# -*- coding: utf-8 -*-
"""Volcar estructura de listado de La Curacao (Magento)."""
import gzip
import re
import ssl
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def get(url):
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding", "").lower() == "gzip":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", "replace")


body = get("https://lacuracaonline.com/guatemala/c/muebles")
print("len:", len(body))

# bloques ld+json
blocks = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', body, re.S)
print("bloques ld+json:", len(blocks))
for i, b in enumerate(blocks[:3]):
    print(f"--- ld+json {i} ---")
    print(b[:600].replace("\n", " "))

# contexto itemprop name
m = re.search(r'itemprop="name"', body)
if m:
    print("\n--- contexto itemprop=name ---")
    print(body[m.start() - 400:m.start() + 400])

# contexto priceCurrency
m2 = re.search(r'"priceCurrency"', body)
if m2:
    print("\n--- contexto priceCurrency ---")
    print(body[m2.start() - 400:m2.start() + 400])
