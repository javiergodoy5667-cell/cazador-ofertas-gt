# -*- coding: utf-8 -*-
"""Diagnostico del formato de URL de producto de Siman."""
import json, ssl, urllib.request, gzip, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def get(url):
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding","").lower()=="gzip":
                raw = gzip.decompress(raw)
            return r.status, r.geturl(), raw.decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, url, ""
    except Exception as e:
        return None, url, f"ERR {type(e).__name__}"

st, fu, body = get("https://www.siman.com/api/catalog_system/pub/products/search?ft=televisor&_from=0&_to=3")
data = json.loads(body)
for p in data:
    print(json.dumps({k: p.get(k) for k in ("productId","productName","linkText","link","origin","productReference")}, ensure_ascii=False, indent=1))
    lt = p.get("linkText")
    for fmt in (f"https://www.siman.com/{lt}/p",
                f"https://www.siman.com/{lt}",
                f"https://www.siman.com/producto/{lt}/p",
                f"https://www.siman.com/gt/{lt}/p"):
        s, fu2, _ = get(fmt)
        print(f"   {s}  {fmt}")
    break
