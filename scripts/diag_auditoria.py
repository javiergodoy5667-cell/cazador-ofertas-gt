# -*- coding: utf-8 -*-
"""Diagnostico para la auditoria: arbol VTEX + HTML de La Curacao."""
import gzip
import json
import re
import ssl
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def get(url):
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding", "").lower() == "gzip":
            raw = gzip.decompress(raw)
        return r.status, raw.decode("utf-8", "replace")


def ids_arbol(nodo, out):
    if isinstance(nodo, dict):
        if "id" in nodo:
            out.append(nodo["id"])
        for c in (nodo.get("children") or []):
            ids_arbol(c, out)
    elif isinstance(nodo, list):
        for c in nodo:
            ids_arbol(c, out)


# --- VTEX arbol ---
st, body = get("https://www.cemaco.com/api/catalog_system/pub/category/tree/3")
print("VTEX tree status:", st, "len:", len(body))
try:
    tree = json.loads(body)
    ids = []
    ids_arbol(tree, ids)
    print("categorias totales (nivel<=3):", len(ids), "| primeras:", ids[:8])
    st2, b2 = get(f"https://www.cemaco.com/api/catalog_system/pub/products/search?fq=C:/{ids[0]}/&_from=0&_to=4")
    d2 = json.loads(b2)
    print("fq=C:/id/ test:", st2, "->", len(d2), "productos")
    if d2:
        print("  ejemplo:", d2[0].get("productName", "")[:50])
except Exception as e:
    print("ERROR arbol:", repr(e), body[:200])

# --- La Curacao (Magento) ---
st, body = get("https://lacuracaonline.com/guatemala/c/muebles")
print("\nLa Curacao status:", st, "len:", len(body))
for pat in ["product-item-info", "product-item-link", "data-price-amount",
            '"priceCurrency"', 'itemprop="name"', "price-box"]:
    print(f"  '{pat}':", body.count(pat))
m = re.search(r'product-item-info', body)
if m:
    print("--- snippet primera tarjeta ---")
    print(body[m.start() - 200:m.start() + 1400])
