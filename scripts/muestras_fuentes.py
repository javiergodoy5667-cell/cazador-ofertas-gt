# -*- coding: utf-8 -*-
"""
Fase 0 - Generador de muestras reales (20 productos por fuente).
Fuentes VTEX usan el API publico de catalogo; Intelaf y Pacifiko usan
sus sitemaps + microdatos ld+json. Solo biblioteca estandar.
Salida: muestras/<slug>.json
"""
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
import gzip
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MUESTRAS = BASE / "muestras"
MUESTRAS.mkdir(exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
TIMEOUT = 20

# ---------------------------------------------------------------------------
# HTTP comun
# ---------------------------------------------------------------------------
def get(url, timeout=TIMEOUT):
    for verify in (True, False):
        ctx = ssl.create_default_context() if verify else ssl._create_unverified_context()
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "application/json,text/html,application/xml,*/*;q=0.9",
            "Accept-Encoding": "gzip",
            "Accept-Language": "es-GT,es;q=0.9,en;q=0.8",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding", "").lower() == "gzip":
                    raw = gzip.decompress(raw)
                return r.status, r.geturl(), raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, url, ""
        except Exception as e:
            if "CERTIFICATE" in str(e).upper():
                continue
            return None, url, ""
    return None, url, ""


def limpiar_precio(v):
    """'Q1,299.00' o '1299.00' -> 1299.0 (float). None si no valido."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("Q", "").replace(",", "").replace(" ", "").strip()
    m = re.search(r"-?\d+(\.\d+)?", s)
    if not m:
        return None
    return float(m.group())


# ---------------------------------------------------------------------------
# VTEX
# ---------------------------------------------------------------------------
VTEX = [
    ("walmart-gt", "Walmart GT", "www.walmart.com.gt", ""),
    ("elektra-gt", "Elektra GT", "www.elektra.com.gt", ""),
    ("cemaco", "Cemaco", "www.cemaco.com", ""),
    ("siman", "Simán", "www.siman.com", "/producto"),
]
TERMINOS = ["televisor", "laptop", "celular", "refrigeradora", "lavadora",
            "zapatos", "taladro", "cocina", "audifonos", "moto"]


def vtex_muestras(host, tienda, slug, prefijo="", max_prod=20):
    seen = {}
    for t in TERMINOS:
        if len(seen) >= max_prod:
            break
        url = (f"https://{host}/api/catalog_system/pub/products/search"
               f"?ft={t}&_from=0&_to=49")
        st, fu, body = get(url)
        if st not in (200, 206) or not body:
            continue
        try:
            data = json.loads(body)
        except Exception:
            continue
        for p in data:
            if len(seen) >= max_prod:
                break
            try:
                pid = p.get("productId")
                if pid in seen:
                    continue
                it = p["items"][0]
                seller = it["sellers"][0]
                offer = seller.get("commertialOffer", {})
                img = (it["images"][0]["imageUrl"] if it.get("images") else None)
                precio = limpiar_precio(offer.get("Price"))
                antes = limpiar_precio(offer.get("ListPrice"))
                if precio is None or precio <= 0:
                    continue
                seen[pid] = {
                    "id": f"{slug}-{pid}",
                    "tienda": tienda,
                    "nombre": p.get("productName", ""),
                    "precio_actual": precio,
                    "precio_antes_tienda": antes,
                    "moneda": "GTQ",
                    "url": f"https://{host}{prefijo}/{p.get('linkText', '')}/p",
                    "imagen": img,
                    "disponible": bool(offer.get("IsAvailable")),
                }
            except (KeyError, IndexError, TypeError):
                continue
    return list(seen.values())


# ---------------------------------------------------------------------------
# Sitemap + ld+json (Intelaf, Pacifiko)
# ---------------------------------------------------------------------------
def sitemap_urls(sitemap_url, filtro):
    st, fu, body = get(sitemap_url)
    if st != 200:
        return []
    locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", body)
    return [u.replace("&amp;", "&") for u in locs if filtro in u]


def ldjson_producto(body):
    """Devuelve dict {nombre, precio, imagen, disponible, url} o None."""
    for b in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
                        body, re.S):
        try:
            obj = json.loads(b)
        except Exception:
            continue
        objs = obj if isinstance(obj, list) else [obj]
        for o in objs:
            if isinstance(o, dict) and o.get("@type") == "Product":
                offers = o.get("offers")
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                if not offers:
                    continue
                precio = limpiar_precio(offers.get("price"))
                if precio is None or precio <= 0:
                    continue
                img = o.get("image")
                if isinstance(img, list):
                    img = img[0] if img else None
                disp = "InStock" in str(offers.get("availability", ""))
                return {
                    "nombre": o.get("name", ""),
                    "precio_actual": precio,
                    "precio_antes_tienda": None,
                    "moneda": (offers.get("priceCurrency") or "GTQ"),
                    "imagen": img,
                    "disponible": disp,
                    "url": offers.get("url"),
                }
    return None


def html_muestras(slug, tienda, sitemap_url, filtro, max_prod=20):
    urls = sitemap_urls(sitemap_url, filtro)
    out = []
    for u in urls:
        if len(out) >= max_prod:
            break
        st, fu, body = get(u)
        if st != 200 or not body:
            continue
        d = ldjson_producto(body)
        if not d:
            continue
        d["id"] = f"{slug}-{len(out)}"
        d["tienda"] = tienda
        d["url"] = d.get("url") or u
        out.append(d)
    return out


# ---------------------------------------------------------------------------
def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    total = {}
    # VTEX
    for slug, tienda, host, prefijo in VTEX:
        r = vtex_muestras(host, tienda, slug, prefijo)
        total[slug] = r
        (MUESTRAS / f"{slug}.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{tienda:<14} VTEX    -> {len(r)} productos")
        if r:
            x = r[0]
            print(f"     ej: {x['nombre'][:60]} | Q{x['precio_actual']} | "
                  f"antes Q{x['precio_antes_tienda']}")

    # Intelaf
    r = html_muestras("intelaf", "Intelaf",
                      "https://www.intelaf.com/sitemap.xml",
                      "/precios_stock_detallado/")
    total["intelaf"] = r
    (MUESTRAS / "intelaf.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Intelaf          HTML    -> {len(r)} productos")
    if r:
        x = r[0]
        print(f"     ej: {x['nombre'][:60]} | Q{x['precio_actual']}")

    # Pacifiko
    r = html_muestras("pacifiko", "Pacifiko",
                      "https://www.pacifiko.com/pids-1.xml",
                      "/compras-en-linea/")
    total["pacifiko"] = r
    (MUESTRAS / "pacifiko.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Pacifiko         HTML    -> {len(r)} productos")
    if r:
        x = r[0]
        print(f"     ej: {x['nombre'][:60]} | Q{x['precio_actual']}")

    print("\nResumen total:", {k: len(v) for k, v in total.items()})


if __name__ == "__main__":
    main()
