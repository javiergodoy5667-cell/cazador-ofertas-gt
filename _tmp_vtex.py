import json, sys
sys.path.insert(0, ".")
from recolectores import _base
for host in ("www.officedepot.com.gt", "www.max.com.gt"):
    u = f"https://{host}/api/catalog_system/pub/products/search?ft=cable&_from=0&_to=2"
    st, _f, b = _base.get(u, host=host, reintentos=1, timeout=20)
    print(host, "->", st, (b[:80] if b else ""))
    if st in (200, 206) and b.startswith("["):
        d = json.loads(b)
        print("   VTEX productos:", len(d))
        if d:
            it = d[0]["items"][0]
            off = it["sellers"][0]["commertialOffer"]
            print("   ej:", d[0]["productName"][:50], "Q", off.get("Price"), "ean", it.get("ean"))
