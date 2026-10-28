# -*- coding: utf-8 -*-
"""Sondeo de tiendas GT: detecta VTEX, Shopify o ld+json y cuenta productos."""
import json
import re
import sys

sys.path.insert(0, ".")
from recolectores import _base

CANDIDATOS = [
    ("Max", "www.max.com.gt"),
    ("Novex", "www.novex.com.gt"),
    ("EPA", "www.epa.com.gt"),
    ("Office Depot GT", "www.officedepot.com.gt"),
    ("Kemik", "www.kemik.gt"),
    ("Spirit Computacion", "www.spirit.com.gt"),
    ("Click", "www.click.com.gt"),
    ("Tecnofacil", "www.tecnofacil.com.gt"),
    ("Sporta", "www.sporta.com.gt"),
    ("Celasa", "www.celasa.com.gt"),
    ("PriceSmart GT", "www.pricesmart.com"),
]


def probar(nombre, host):
    # 1) VTEX
    url = f"https://{host}/api/catalog_system/pub/products/search?ft=cable&_from=0&_to=1"
    st, _fu, body = _base.get(url, host=host, reintentos=1, timeout=15)
    if st in (200, 206) and body.startswith("["):
        try:
            data = json.loads(body)
            print(f"  {nombre:<18} VTEX OK  ({len(data)} en la muestra)  {host}")
            return "vtex"
        except Exception:
            pass
    # 2) Shopify
    url = f"https://{host}/products.json?limit=2"
    st, _fu, body = _base.get(url, host=host, reintentos=1, timeout=15)
    if st == 200 and '"products"' in body:
        try:
            data = json.loads(body)
            print(f"  {nombre:<18} SHOPIFY OK ({len(data.get('products', []))})  {host}")
            return "shopify"
        except Exception:
            pass
    # 3) ld+json
    st, _fu, body = _base.get(f"https://{host}/", host=host, reintentos=1, timeout=15)
    if st == 200 and "ld+json" in body:
        tipos = re.findall(r'"@type"\s*:\s*"(\w+)"', body)
        print(f"  {nombre:<18} HTML+ld+json ({len(body)} bytes, tipos={set(tipos[:5])})  {host}")
        return "html"
    print(f"  {nombre:<18} NO ({st})  {host}")
    return None


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for nombre, host in CANDIDATOS:
        probar(nombre, host)
