# -*- coding: utf-8 -*-
"""
Fase 0 - Sondeo de fuentes guatemaltecas (v2).
Mejoras: fallback a SSL sin verificar, prueba www., mejor deteccion VTEX.
Solo biblioteca estandar.
"""

import concurrent.futures as cf
import datetime as dt
import gzip
import json
import re
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MUESTRAS = BASE / "muestras"
MUESTRAS.mkdir(exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
TIMEOUT = 20

# nombre -> lista de hosts (sin https://). Se prueba tal cual y con www.
CANDIDATAS = [
    ("Walmart GT",      ["walmart.com.gt"]),
    ("La Torre",        ["latorre.com.gt"]),
    ("La Curacao GT",   ["lacuracaonline.com"]),
    ("Elektra GT",      ["elektra.com.gt"]),
    ("Tiendas Max",     ["max.com.gt"]),
    ("Intelaf",         ["intelaf.com"]),
    ("Pacifiko",        ["pacifiko.com"]),
    ("Simán",           ["siman.com"]),
    ("Cemaco",          ["cemaco.com"]),
    ("Novex",           ["novex.com.gt"]),
    ("Agencias Way",    ["agenciasway.com.gt"]),
    ("Super 24",        ["super24.com.gt"]),
    ("Kemik",           ["kemik.gt"]),
    ("PriceSmart GT",   ["pricesmart.com"]),
    ("Office Depot GT", ["officedepot.com.gt"]),
]


def fetch(url, timeout=TIMEOUT, max_redir=6):
    """GET con reintento SSL sin verificar. Devuelve dict."""
    for verify in (True, False):
        try:
            ctx = ssl.create_default_context() if verify else ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip",
                "Accept-Language": "es-GT,es;q=0.9,en;q=0.8",
            })
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding", "").lower() == "gzip":
                    raw = gzip.decompress(raw)
                return {"status": r.status, "final_url": r.geturl(),
                        "ctype": r.headers.get("Content-Type", ""),
                        "len": len(raw),
                        "body": raw.decode("utf-8", "replace"),
                        "error": None,
                        "ssl_sin_verificar": not verify}
        except urllib.error.HTTPError as e:
            return {"status": e.code, "final_url": url, "ctype": "",
                    "len": 0, "body": "", "error": f"HTTP {e.code}",
                    "ssl_sin_verificar": not verify}
        except urllib.error.URLError as e:
            reason = getattr(e, "reason", e)
            if isinstance(reason, ssl.SSLCertVerificationError):
                continue  # probar sin verificar
            return {"status": None, "final_url": url, "ctype": "",
                    "len": 0, "body": "", "error": str(reason),
                    "ssl_sin_verificar": not verify}
        except Exception as e:
            return {"status": None, "final_url": url, "ctype": "",
                    "len": 0, "body": "", "error": f"{type(e).__name__}: {e}",
                    "ssl_sin_verificar": not verify}
    return {"status": None, "final_url": url, "ctype": "", "len": 0,
            "body": "", "error": "SSL no verificado tambien fallo",
            "ssl_sin_verificar": True}


def dns_ok(host):
    try:
        socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        return True
    except Exception:
        return False


def vtex_detectar(host, path_pref=""):
    """Prueba el catalogo publico de VTEX. Devuelve dict o None."""
    base = f"https://{host}{path_pref}"
    info = {}
    for url in (f"{base}/api/catalog_system/pub/products/search?ft=televisor&_from=0&_to=9",
                f"{base}/api/catalog_system/pub/products/search?fq=C&_from=0&_to=9"):
        r = fetch(url, timeout=15)
        info["status"] = r["status"]
        info["error"] = r["error"]
        if r["status"] == 200 and r["body"].lstrip()[:1] in ("[", "{"):
            try:
                data = json.loads(r["body"])
                items = data if isinstance(data, list) else data.get("items", [])
                if items:
                    info["productos"] = len(items)
                    info["url"] = url
                    return info
            except Exception:
                pass
        elif r["status"] == 200:
            info["body_inicio"] = r["body"][:120]
    return info


def shopify_detectar(host):
    r = fetch(f"https://{host}/products.json?limit=5", timeout=15)
    if r["status"] == 200:
        try:
            d = json.loads(r["body"])
            if "products" in d:
                return {"productos": len(d["products"])}
        except Exception:
            pass
    return None


def sondear(nombre, hosts):
    out = {"nombre": nombre, "hosts": hosts, "elegido": None,
           "portada": None, "robots": None, "plataforma": None,
           "veredicto": None, "notas": []}

    candidatos = []
    for h in hosts:
        if h not in candidatos:
            candidatos.append(h)
        w = f"www.{h}"
        if w not in candidatos:
            candidatos.append(w)

    for host in candidatos:
        if not dns_ok(host):
            out["notas"].append(f"{host}: DNS no resuelve")
            continue
        home = fetch(f"https://{host}/")
        if home["status"] is None or (home["status"] and home["status"] >= 500):
            out["notas"].append(f"{host}: {home['error']}")
            continue
        out["elegido"] = host
        out["portada"] = {"host": host, "status": home["status"],
                          "final_url": home["final_url"], "len": home["len"],
                          "ssl_sin_verificar": home.get("ssl_sin_verificar"),
                          "error": home["error"]}
        m = re.search(r"<title[^>]*>(.*?)</title>", home["body"], re.I | re.S)
        out["portada"]["titulo"] = (m.group(1).strip()[:120] if m else "")

        rb = fetch(f"https://{host}/robots.txt")
        if rb["status"] == 200:
            disallow = re.findall(r"^\s*Disallow:\s*(\S+)", rb["body"], re.I | re.M)
            out["robots"] = {"status": 200, "disallow": disallow[:12],
                             "bloquea_api": any(a.startswith("/api") for a in disallow),
                             "bloquea_todo": any(a == "/" for a in disallow)}
        else:
            out["robots"] = {"status": rb["status"], "disallow": []}

        plat = {}
        vtex = vtex_detectar(host)
        if vtex and vtex.get("productos"):
            plat["vtex"] = vtex
        else:
            plat["vtex_status"] = vtex
        sh = shopify_detectar(host)
        if sh:
            plat["shopify"] = sh
        sm = fetch(f"https://{host}/sitemap.xml")
        if sm["status"] == 200:
            plat["sitemap_urls"] = sm["body"].count("<loc>")
        body = home["body"].lower()
        firmas = {k: True for k in
                  ("vtex", "shopify", "magento", "woocommerce", "cloudflare",
                   "captcha", "just a moment", "__next_data__", "nuxt", "sap")
                  if k in body}
        plat["firmas"] = firmas
        plat["ld_json"] = body.count("application/ld+json")
        plat["ld_json_precio"] = ('"price"' in body or '"priceCurrency"' in body)
        out["plataforma"] = plat
        break
    return out


def veredicto(s):
    if not s["elegido"]:
        return "❌ descartar (no responde)"
    p = s["plataforma"] or {}
    if p.get("vtex"):
        return f"✅ usar (VTEX, {p['vtex']['productos']} prod de prueba)"
    if p.get("shopify"):
        return f"✅ usar (Shopify, {p['shopify']['productos']} prod)"
    if p.get("firmas", {}).get("vtex") and p.get("sitemap_urls", 0) > 100:
        return "⚠️ VTEX probable; verificar API manualmente"
    if p.get("firmas", {}).get("woocommerce"):
        return "⚠️ usar scraping HTML"
    if s["robots"] and s["robots"].get("bloquea_todo"):
        return "❌ descartar (robots.txt bloquea todo)"
    if p.get("firmas", {}).get("captcha") and not p.get("vtex") and not p.get("shopify"):
        return "❌ descartar (anti-bot)"
    if s["portada"]["len"] < 3000 and not p.get("vtex") and not p.get("shopify"):
        return "❌ descartar (JS shell / sin contenido)"
    return "⚠️ usar scraping HTML (revisar)"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    res = []
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(sondear, n, h): n for n, h in CANDIDATAS}
        for f in cf.as_completed(futs):
            s = f.result()
            s["veredicto"] = veredicto(s)
            res.append(s)
    order = {n: i for i, (n, _) in enumerate(CANDIDATAS)}
    res.sort(key=lambda x: order.get(x["nombre"], 99))

    out = MUESTRAS / f"sondeo_{dt.datetime.now():%Y%m%d-%H%M%S}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'TIENDA':<16} {'HOST':<22} {'PORT':<6} {'SSL':<8} {'PLATAFORMA':<14} VEREDICTO")
    print("-" * 120)
    for s in res:
        host = s["elegido"] or "-"
        st = s["portada"]["status"] if s["portada"] else "-"
        sslx = ("no-verif" if (s["portada"] or {}).get("ssl_sin_verificar") else "ok")
        p = s["plataforma"] or {}
        plat = ""
        if p.get("vtex"):
            plat = f"VTEX({p['vtex']['productos']})"
        elif p.get("shopify"):
            plat = f"Shopify({p['shopify']['productos']})"
        elif p.get("firmas"):
            plat = ",".join(k for k in p["firmas"] if k in
                            ("vtex", "shopify", "woocommerce", "magento", "cloudflare", "nuxt", "__next_data__"))[:14] or "-"
        print(f"{s['nombre']:<16} {host:<22} {str(st):<6} {sslx:<8} {plat:<14} {s['veredicto']}")
    print(f"\nDetalle: {out}")


if __name__ == "__main__":
    main()
