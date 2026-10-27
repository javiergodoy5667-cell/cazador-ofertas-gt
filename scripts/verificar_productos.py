# -*- coding: utf-8 -*-
"""Extraer URLs de producto desde sitemaps y comprobar si el precio
esta en el HTML estatico (server-rendered) o necesita JavaScript."""
import ssl, urllib.request, gzip, re, json, sys

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def get(url, t=20):
    for verify in (True, False):
        ctx = ssl.create_default_context() if verify else ssl._create_unverified_context()
        req = urllib.request.Request(url, headers={"User-Agent": UA,
            "Accept": "text/html,application/xml,application/json,*/*",
            "Accept-Encoding": "gzip", "Accept-Language": "es-GT,es;q=0.9"})
        try:
            with urllib.request.urlopen(req, timeout=t, context=ctx) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding","").lower()=="gzip":
                    raw = gzip.decompress(raw)
                return r.status, r.geturl(), raw.decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            return e.code, url, ""
        except Exception as e:
            if "CERTIFICATE" in str(e).upper():
                continue
            return None, url, f"ERR {type(e).__name__}"
    return None, url, "SSL"

def locs(url):
    st, fu, body = get(url)
    if st != 200:
        return st, []
    return st, re.findall(r"<loc>\s*(.*?)\s*</loc>", body)

def es_producto(u):
    u = u.lower()
    return bool(re.search(r"(/p/|/product|/producto|/products|/item|/pd/|/\d+$|-[0-9]{4,})", u))

def revisar(nombre, sitemap_url, max_urls=6):
    print(f"\n===== {nombre} =====")
    st, ls = locs(sitemap_url)
    print(f"  sitemap {st} -> {len(ls)} locs")
    # si son sitemaps hijo, bajar el primero
    prods = []
    if ls and es_producto(ls[0]) is False and ("sitemap" in ls[0] or ls[0].endswith(".xml")):
        for child in ls[:4]:
            cst, cls = locs(child)
            prods += [u for u in cls if es_producto(u)]
            if len(prods) >= max_urls:
                break
    else:
        prods = [u for u in ls if es_producto(u)]
    prods = prods[:max_urls]
    print(f"  productos candidatos: {len(prods)}")
    for p in prods[:3]:
        st, fu, body = get(p)
        if not body:
            print(f"    {p} -> {st} (vacio)")
            continue
        m = re.search(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', body, re.S)
        ld_price = ('"price"' in body or '"priceCurrency"' in body or '"lowPrice"' in body)
        has_q = re.search(r'Q\s?[\d,\.]+\s?\.?\d{2}', body)
        tit = re.search(r"<title[^>]*>(.*?)</title>", body, re.S)
        print(f"    {st} {p[:70]}")
        print(f"        title={ (tit.group(1).strip()[:60] if tit else '-') }")
        print(f"        ld_json={'si' if m else 'no'}  ld_precio={'si' if ld_price else 'no'}  Q_precio={'si' if has_q else 'no'}")

revisar("Intelaf", "https://www.intelaf.com/sitemap.xml")
revisar("Novex", "https://www.novex.com.gt/catalog-desktop.xml")
revisar("Tiendas Max", "https://www.max.com.gt/sitemap-0.xml")
revisar("Pacifiko", "https://www.pacifiko.com/pids-1.xml")
