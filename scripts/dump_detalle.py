# -*- coding: utf-8 -*-
import ssl, urllib.request, gzip, re, json, sys

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def get(url, t=20):
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA,
        "Accept": "text/html,application/xml,*/*", "Accept-Encoding": "gzip",
        "Accept-Language": "es-GT,es;q=0.9"})
    with urllib.request.urlopen(req, timeout=t, context=ctx) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding","").lower()=="gzip":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8","replace")

# Pacifiko: primer producto real del sitemap
sm = get("https://www.pacifiko.com/pids-1.xml")
locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", sm)
prod = locs[0]
print("### Pacifiko producto:", prod)
body = get(prod)
blocks = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', body, re.S)
print(f"bloques ld+json: {len(blocks)}")
for b in blocks[:1]:
    try:
        print(json.dumps(json.loads(b), ensure_ascii=False, indent=2)[:1400])
    except Exception as e:
        print("no json:", b[:400])

# La Curacao categoria
print("\n\n### La Curacao /guatemala/c/muebles")
body = get("https://lacuracaonline.com/guatemala/c/muebles")
for pat in ['class="product-item', 'data-product-id', 'itemprop="name"', 'class="price', '"priceCurrency"', 'data-price']:
    print(f"  '{pat}' -> {len(re.findall(re.escape(pat), body))}")
m = re.search(r'class="product-item', body)
if m:
    print(body[m.start():m.start()+1600])
