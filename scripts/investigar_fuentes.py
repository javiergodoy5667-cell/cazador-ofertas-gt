# -*- coding: utf-8 -*-
"""Investigar plataforma de las fuentes que NO son VTEX."""
import ssl, urllib.request, gzip, re, sys

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def get(url, t=18):
    for verify in (True, False):
        ctx = ssl.create_default_context() if verify else ssl._create_unverified_context()
        req = urllib.request.Request(url, headers={"User-Agent": UA,
            "Accept": "text/html,application/json,*/*", "Accept-Encoding": "gzip",
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
    return None, url, "", "SSL"

def show_sitemap(host):
    st, fu, ct, body = get(f"https://{host}/sitemap.xml")
    if st != 200:
        print(f"  sitemap.xml -> {st}")
        return
    locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", body)
    print(f"  sitemap.xml -> {len(locs)} locs")
    for l in locs[:8]:
        print(f"      {l}")

def show_robots(host):
    st, fu, ct, body = get(f"https://{host}/robots.txt")
    if st == 200:
        dis = re.findall(r"^\s*Disallow:\s*(\S*)", body, re.I | re.M)
        print(f"  robots disallow: {dis[:10]}")

def probe(host, extra_paths=()):
    print(f"\n===== {host} =====")
    st, fu, ct, home = get(f"https://{host}/")
    print(f"  home {st} len={len(home)}")
    show_robots(host)
    show_sitemap(host)
    for p in ("/products.json?limit=2", "/graphql", "/wp-json/wp/v2/posts?per_page=1",
              "/rest/V1/products?searchCriteria[pageSize]=1", "/api/products"):
        st, fu, ct, body = get(f"https://{host}{p}")
        if st is not None:
            snippet = body[:90].replace("\n"," ")
            print(f"  {p} -> {st} {ct[:30]} | {snippet}")
    for p in extra_paths:
        st, fu, ct, body = get(f"https://{host}{p}")
        if st is not None:
            m = re.search(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', body, re.S)
            precio_en_html = 'precio' in body.lower() or '"price"' in body.lower()
            print(f"  {p} -> {st} len={len(body)} ldjson={'si' if m else 'no'} precio={'si' if precio_en_html else 'no'} | {body[:80].strip()[:80]!r}")

probe("www.intelaf.com")
probe("www.pacifiko.com")
probe("lacuracaonline.com", ["/guatemala/c/muebles"])
probe("novex.com.gt")
probe("max.com.gt")
