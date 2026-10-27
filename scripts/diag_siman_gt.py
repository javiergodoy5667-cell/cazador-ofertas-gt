# -*- coding: utf-8 -*-
"""Verificar dominio de Siman Guatemala (quetzales) y links de producto."""
import json
import ssl
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def get(url):
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
            return r.status, r.geturl(), r.read().decode("utf-8", "replace")
    except Exception as e:
        return None, url, f"ERR {type(e).__name__}: {e}"


HOST = "simanguatemala.vtexcommercestable.com.br"
st, fu, body = get(f"https://{HOST}/api/catalog_system/pub/products/search?ft=microondas&_from=0&_to=2")
print("API GT:", st, fu)
if body.startswith("["):
    data = json.loads(body)
    for p in data[:3]:
        item = p["items"][0]
        off = item["sellers"][0]["commertialOffer"]
        print(f"  {p['productName'][:45]} | Price={off.get('Price')} ListPrice={off.get('ListPrice')} ean={item.get('ean')}")
        print(f"    linkText={p.get('linkText')}")

print("\n--- probar dominios de storefront ---")
for dom in ("simanguatemala.com", "simanguatemala.com.gt", "www.simanguatemala.com",
            "siman.com"):
    st, fu, body = get(f"https://{dom}/")
    print(f"  {dom:<32} -> {st} {body[:60] if st else body[:60]}")
