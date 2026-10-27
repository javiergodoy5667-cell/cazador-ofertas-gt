# -*- coding: utf-8 -*-
"""Diagnostico del API publico de VTEX para varias tiendas."""
import json, ssl, urllib.request, gzip, sys

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def get(url, t=15):
    for verify in (True, False):
        ctx = ssl.create_default_context() if verify else ssl._create_unverified_context()
        req = urllib.request.Request(url, headers={"User-Agent": UA,
            "Accept": "application/json,text/html,*/*", "Accept-Encoding": "gzip",
            "Accept-Language": "es-GT,es;q=0.9"})
        try:
            with urllib.request.urlopen(req, timeout=t, context=ctx) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding","").lower()=="gzip":
                    raw = gzip.decompress(raw)
                return r.status, r.geturl(), r.headers.get("Content-Type",""), raw.decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            return e.code, url, "", ""
        except Exception as e:
            if "CERTIFICATE" in str(e).upper():
                continue
            return None, url, "", f"ERR {type(e).__name__}: {e}"
    return None, url, "", "SSL fallo"

hosts = ["www.cemaco.com", "www.elektra.com.gt", "www.pacifiko.com",
         "www.siman.com", "www.intelaf.com", "www.walmart.com.gt",
         "lacuracaonline.com"]
paths = [
    "/api/catalog_system/pub/products/search?ft=televisor&_from=0&_to=2",
    "/api/catalog_system/pub/products/search/televisor?&_from=0&_to=2",
    "/api/catalog_system/pub/products/search?fq=tele&_from=0&_to=2",
]
for h in hosts:
    print(f"\n===== {h} =====")
    for p in paths:
        st, fu, ct, body = get(f"https://{h}{p}")
        snippet = body[:200].replace("\n", " ")
        print(f"  {st} {p}  -> ct={ct}  | {snippet}")
