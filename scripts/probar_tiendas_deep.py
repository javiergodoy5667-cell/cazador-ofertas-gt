# -*- coding: utf-8 -*-
"""Sondeo profundo: busca Product ld+json en paginas de listado y pistas de API."""
import json
import re
import sys

sys.path.insert(0, ".")
from recolectores import _base


def pistas(nombre, host):
    st, _fu, body = _base.get(f"https://{host}/", host=host, reintentos=1, timeout=15)
    if st != 200:
        print(f"{nombre}: home {st}")
        return
    low = body.lower()
    señales = [s for s in ("vtex", "shopify", "magento", "woocommerce", "prestashop",
                            "bcapp", "bigcommerce", "salesforce", "sap") if s in low]
    print(f"{nombre}: {len(body)} bytes; plataforma~{señales}")


def product_ldjson(nombre, host, path):
    st, _fu, body = _base.get(f"https://{host}{path}", host=host, reintentos=1, timeout=20)
    if st != 200:
        print(f"{nombre} {path}: {st}")
        return
    bloques = re.findall(r'<script[^>]*ld\+json[^>]*>(.*?)</script>', body, re.S | re.I)
    total = 0
    for b in bloques:
        try:
            data = json.loads(b.strip())
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict) and it.get("@type") == "Product":
                total += 1
    print(f"{nombre} {path}: {len(body)} bytes, Product ld+json={total}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for nombre, host in (("Max", "www.max.com.gt"), ("EPA", "www.epa.com.gt"),
                         ("EPA2", "epa.com.gt"), ("OfficeDepot", "www.officedepot.com.gt"),
                         ("Celasa", "www.celasa.com.gt"), ("Tecnofacil", "www.tecnofacil.com.gt")):
        pistas(nombre, host)
    print()
    # paginas de listado tipicas
    for nombre, host, path in (
        ("Novex", "www.novex.com.gt", "/herramientas"),
        ("Novex", "www.novex.com.gt", "/categoria/herramientas"),
        ("Sporta", "www.sporta.com.gt", "/productos"),
        ("Sporta", "www.sporta.com.gt", "/tienda"),
    ):
        product_ldjson(nombre, host, path)
